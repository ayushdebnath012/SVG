"""Constrained tool-using verifier policy; labels are never used to build observations."""
import json

ACTIONS = ('execute', 'numbers', 'accept', 'reject')
SYSTEM = '''You verify whether a CAD edit fulfills the instruction and preserves unrelated features.
Choose one next action, exactly one letter:
A: execute the candidate CAD and inspect validity, volume and change from source.
B: inspect numeric instruction checks against the patch.
C: accept the candidate as correct.
D: reject the candidate and request repair.
Tool validity and numeric checks are partial evidence, not proof of correctness.
Use the source, instruction and patch to judge semantics. Only available actions may be chosen.'''


def available(state):
    return [0, 1] if state == 0 else [i for i in range(4) if i >= 2 or not state & (1 << i)]


def messages(row, state):
    # Explicit whitelist: never serialize label, reference, target or audit fields.
    observation = {'instruction': row['instruction'], 'source': row['code'], 'candidate': row['candidate']}
    history = []
    for i, tool in enumerate(ACTIONS[:2]):
        if state & (1 << i):
            history.append({'tool': tool, 'result': row['tools'][tool]})
    observation['tool_results'] = history
    observation['available_actions'] = ['ABCD'[i] for i in available(state)]
    return [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': json.dumps(observation)}]


def reward(label, action, tool_calls):
    if action not in (2, 3):
        raise ValueError('A terminal verdict is required')
    correct = (action == 2) == bool(label)
    return (1.0 if correct else (-2.0 if action == 2 else -1.0)) - .02 * tool_calls


def rollout(probabilities, label, rng=None):
    state, trace = 0, []
    while True:
        allowed = available(state)
        p = [probabilities[state][a] for a in allowed]
        action = allowed[max(range(len(p)), key=lambda j: p[j])] if rng is None else rng.choices(allowed, weights=p)[0]
        trace.append((state, action))
        if action >= 2:
            return {'trace': trace, 'accepted': action == 2, 'reward': reward(label, action, len(trace)-1)}
        state |= 1 << action


def model_logits(model, encoded, action_ids):
    # Only the final position needs vocabulary logits; avoid B*T*vocab allocation.
    import torch
    sequence = model.base_model.model.model(**encoded).last_hidden_state
    last = encoded['attention_mask'].sum(-1) - 1
    hidden = sequence[torch.arange(sequence.shape[0], device=sequence.device), last]
    return model.get_output_embeddings()(hidden).float()[:, action_ids]
