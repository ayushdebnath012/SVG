from __future__ import annotations

from typing import Any


class GNNUnavailable(RuntimeError):
    pass


def _torch_dependencies():
    try:
        import torch
        import torch.nn as nn
    except ImportError as exc:
        raise GNNUnavailable("GNN requires: pip install torch") from exc
    return torch, nn


class NodeGNN:
    """Graph neural network over the SVG DOM for per-node relevance scoring.

    Plan A Stage 3-4: takes per-node ViT embeddings + scene graph structure
    and produces a relevance score per node for a given edit instruction.

    The GNN passes messages along parent-child and sibling edges. An LSTM
    accumulates ancestor-chain context. A small MLP head produces the final
    scalar relevance score per node.

    Training is done separately via train/sft_decomposer.py (fine-tuning on
    labeled target-selection examples). This class handles inference only.
    """

    def __init__(
        self,
        embed_dim: int = 768,
        text_dim: int = 256,
        hidden_dim: int = 256,
        num_layers: int = 2,
    ):
        self.embed_dim = embed_dim
        self.text_dim = text_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self._net: Any = None

    def _build_net(self) -> None:
        if self._net is not None:
            return
        torch, nn = _torch_dependencies()

        class _Net(nn.Module):
            def __init__(self, embed_dim: int, text_dim: int, hidden_dim: int):
                super().__init__()
                self.node_proj = nn.Linear(embed_dim, hidden_dim)
                self.lstm = nn.LSTM(hidden_dim, hidden_dim, batch_first=True)
                self.message_proj = nn.Linear(hidden_dim * 2, hidden_dim)
                self.head = nn.Sequential(
                    nn.Linear(hidden_dim + text_dim, hidden_dim),
                    nn.ReLU(),
                    nn.Linear(hidden_dim, 1),
                    nn.Sigmoid(),
                )

            def forward(self, node_feats, adj, text_feat):
                h = torch.relu(self.node_proj(node_feats))
                # single message-passing round over adjacency matrix
                agg = torch.bmm(adj, h)
                h = torch.relu(self.message_proj(torch.cat([h, agg], dim=-1)))
                text_expanded = text_feat.unsqueeze(1).expand(-1, h.size(1), -1)
                scores = self.head(torch.cat([h, text_expanded], dim=-1))
                return scores.squeeze(-1)

        self._net = _Net(self.embed_dim, self.text_dim, self.hidden_dim)

    def load_weights(self, path: str) -> None:
        """Load trained weights from a checkpoint file."""
        torch, _ = _torch_dependencies()
        self._build_net()
        state = torch.load(path, map_location="cpu")
        self._net.load_state_dict(state)
        self._net.eval()

    def score_nodes(
        self,
        node_embeddings: dict[str, list[float]],
        scene: dict,
        instruction_embedding: list[float],
    ) -> dict[str, float]:
        """Return a relevance score in [0, 1] per node ID.

        node_embeddings: output of NodeEmbedder.embed_all()
        scene: output of build_scene()
        instruction_embedding: text embedding of the edit instruction
            (e.g. from a sentence-transformer or the LM's encoder)
        """
        torch, _ = _torch_dependencies()
        self._build_net()

        nodes = scene["nodes"]
        node_ids = [n["id"] for n in nodes]
        n = len(node_ids)
        idx = {nid: i for i, nid in enumerate(node_ids)}

        feat_dim = self.embed_dim
        feats = torch.zeros(1, n, feat_dim)
        for i, nid in enumerate(node_ids):
            if nid in node_embeddings:
                feats[0, i] = torch.tensor(node_embeddings[nid][:feat_dim])

        adj = torch.zeros(1, n, n)
        for node in nodes:
            parent = node.get("parent")
            if parent and parent in idx:
                i, j = idx[node["id"]], idx[parent]
                adj[0, i, j] = 1.0
                adj[0, j, i] = 1.0

        text_feat = torch.zeros(1, self.text_dim)
        emb = instruction_embedding[: self.text_dim]
        text_feat[0, : len(emb)] = torch.tensor(emb)

        with torch.no_grad():
            scores = self._net(feats, adj, text_feat)[0]

        return {nid: float(scores[i]) for i, nid in enumerate(node_ids)}

    def select_targets(
        self, scores: dict[str, float], threshold: float = 0.5
    ) -> list[str]:
        """Return node IDs above threshold, sorted by descending score."""
        return sorted(
            (nid for nid, s in scores.items() if s >= threshold),
            key=lambda nid: scores[nid],
            reverse=True,
        )
