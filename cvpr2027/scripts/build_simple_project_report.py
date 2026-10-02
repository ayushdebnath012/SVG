"""Build the plain-language project report as a polished PDF."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Image, HRFlowable
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/pdf/engineering_svg_project_report.pdf"

NAVY = colors.HexColor("#17324D")
BLUE = colors.HexColor("#2F6F91")
PALE = colors.HexColor("#EAF3F8")
INK = colors.HexColor("#18222C")
MUTED = colors.HexColor("#5B6770")
GRID = colors.HexColor("#D9D9D9")


def fonts():
    candidates = [
        ("/System/Library/Fonts/Supplemental/Arial.ttf", "Arial"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "DejaVu"),
    ]
    for path, name in candidates:
        if Path(path).exists():
            pdfmetrics.registerFont(TTFont("Body", path))
            bold = path.replace("Arial.ttf", "Arial Bold.ttf").replace("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")
            if Path(bold).exists():
                pdfmetrics.registerFont(TTFont("BodyBold", bold))
            else:
                pdfmetrics.registerFont(TTFont("BodyBold", path))
            return
    raise RuntimeError("No supported font found")


fonts()

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="ReportTitle", fontName="BodyBold", fontSize=26, leading=31,
                          textColor=colors.black, spaceAfter=18, alignment=TA_LEFT))
styles.add(ParagraphStyle(name="Subtitle", fontName="Body", fontSize=13, leading=19,
                          textColor=MUTED, spaceAfter=18))
styles.add(ParagraphStyle(name="H1x", fontName="BodyBold", fontSize=18, leading=23,
                          textColor=colors.black, spaceBefore=10, spaceAfter=10, keepWithNext=True))
styles.add(ParagraphStyle(name="H2x", fontName="BodyBold", fontSize=13, leading=17,
                          textColor=colors.black, spaceBefore=9, spaceAfter=5, keepWithNext=True))
styles.add(ParagraphStyle(name="Bodyx", fontName="Body", fontSize=10.5, leading=15.5,
                          textColor=INK, spaceAfter=8))
styles.add(ParagraphStyle(name="Lead", fontName="Body", fontSize=12, leading=18,
                          textColor=INK, spaceAfter=12))
styles.add(ParagraphStyle(name="Small", fontName="Body", fontSize=8.7, leading=12,
                          textColor=MUTED, spaceAfter=5))
styles.add(ParagraphStyle(name="Bulletx", fontName="Body", fontSize=10.2, leading=14.5,
                          leftIndent=15, firstLineIndent=-9, bulletIndent=3, textColor=INK, spaceAfter=5))
styles.add(ParagraphStyle(name="TableHead", fontName="BodyBold", fontSize=8.6, leading=11,
                          textColor=colors.white, alignment=TA_CENTER))
styles.add(ParagraphStyle(name="TableBody", fontName="Body", fontSize=8.3, leading=11,
                          textColor=INK))
styles.add(ParagraphStyle(name="TableCenter", fontName="Body", fontSize=8.3, leading=11,
                          textColor=INK, alignment=TA_CENTER))
styles.add(ParagraphStyle(name="Quote", fontName="Body", fontSize=10.5, leading=15.5,
                          leftIndent=18, rightIndent=18, textColor=NAVY, spaceBefore=5, spaceAfter=10))


def P(text, style="Bodyx"):
    return Paragraph(text, styles[style])


def bullet(text):
    return Paragraph("• " + text, styles["Bulletx"])


def table(rows, widths, center_cols=()):
    cooked = []
    for r, row in enumerate(rows):
        cooked.append([
            Paragraph(str(cell), styles["TableHead"] if r == 0 else
                      (styles["TableCenter"] if c in center_cols else styles["TableBody"]))
            for c, cell in enumerate(row)
        ])
    t = Table(cooked, colWidths=widths, repeatRows=1, hAlign="LEFT")
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.5, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    for r in range(1, len(rows)):
        commands.append(("BACKGROUND", (0, r), (-1, r), colors.white if r % 2 else PALE))
    t.setStyle(TableStyle(commands))
    return t


def architecture_table():
    rows = [
        [P("1  Input drawing", "TableHead"), P("2  Meaning model", "TableHead"), P("3  Engineering checks", "TableHead"), P("4  Final evidence", "TableHead")],
        [P("Dimensioned SVG, edit instruction, geometry, notes and views", "TableBody"),
         P("Members, sections, loads, supports, dimensions and relationships", "TableBody"),
         P("Geometry rules, FEM, buckling, mass, manufacturing or other domain checks", "TableBody"),
         P("Updated SVG, measurements, pass or fail results, assumptions and unresolved ambiguity", "TableBody")],
    ]
    t = Table(rows, colWidths=[1.66*inch]*4, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("GRID", (0, 0), (-1, -1), 0.7, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BACKGROUND", (0, 1), (-1, 1), PALE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    return t


class ReportDoc(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(filename, pagesize=letter, leftMargin=.78*inch, rightMargin=.78*inch,
                         topMargin=.76*inch, bottomMargin=.68*inch,
                         title="Engineering SVG Drawing Project Report",
                         author="Engineering SVG Research Project")
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="normal")
        self.addPageTemplates(PageTemplate(id="main", frames=frame, onPage=self.header_footer))

    def header_footer(self, canvas, doc):
        canvas.saveState()
        if doc.page > 1:
            canvas.setFont("Body", 8)
            canvas.setFillColor(MUTED)
            canvas.drawString(self.leftMargin, letter[1]-.42*inch, "Engineering SVG Drawing Project Report")
            canvas.drawRightString(letter[0]-self.rightMargin, .38*inch, f"Page {doc.page}")
            canvas.setStrokeColor(GRID)
            canvas.line(self.leftMargin, letter[1]-.48*inch, letter[0]-self.rightMargin, letter[1]-.48*inch)
        canvas.restoreState()


story = []
story += [Spacer(1, .65*inch), P("Engineering SVG Drawing Project Report", "ReportTitle"),
          P("A plain language account of the problem, system architecture, experiments, results and research direction", "Subtitle"),
          HRFlowable(width="100%", thickness=2, color=BLUE, spaceBefore=4, spaceAfter=24),
          P("Project status", "H2x"),
          P("Research foundation completed through 22 September 2026. The project is not yet ready for a paper submission or production use.", "Lead"),
          P("Main finding", "H2x"),
          P("We built a working pipeline for engineering object drawings and tested it on frames, plates, rolled sheet patterns, machining drawings and released CAD examples. Astra passed every fully scored new functional design case. This means the current experiments do not identify a repeatable Astra weakness that would justify targeted training.", "Lead"),
          Spacer(1, .35*inch),
          P("Prepared from the project source code, saved API trials, verification reports and a 67 record literature and dataset registry.", "Small"),
          PageBreak()]

story += [P("Executive Summary", "H1x"),
          P("The project studies AI systems that create or edit real engineering object drawings. Examples include a building frame, a table, a machined plate or a sheet metal part. The output is an SVG or CAD style drawing that carries dimensions and engineering meaning.", "Lead"),
          P("A drawing can look correct while describing an unsafe, impossible or internally inconsistent object. The project therefore connects the drawing to checks that fit the object. A structural frame may need finite element analysis and buckling checks. A machined part may need solid geometry and feature checks. A sheet metal pattern may need a flat to folded geometry check. Dimensions, labels and multiple views must also agree.", "Bodyx"),
          P("The completed work provides a reproducible evaluation base. It includes deterministic graders, physics checks, saved model interactions, classical search controls, released-data probes and a literature audit. It does not yet provide a confirmed failure set for training. Six new structural sizing tasks all passed Astra, including cases with only one or two acceptable assignments among thousands or millions of possibilities.", "Bodyx"),
          P("Recommended decision", "H2x"),
          P("Keep the passing tasks as control cases. Do not train on them as if they were Astra failures. The next benchmark should focus on detached engineering drawings where the original CAD relationships are missing and the visible drawing may allow different valid edits. This direction still needs a larger dataset and a demonstrated gap against strong models and rule based systems.", "Bodyx"),
          Spacer(1, 6),
          table([
              ["Completed area", "Evidence", "Current conclusion"],
              ["Functional structural design", "6 of 6 Astra passes", "Useful control set, no hard case"],
              ["Custom drawing screens", "5 of 5 passes", "No hard case"],
              ["Released complex CAD", "38 and 11 local checks passed", "Full shapes remain unscored"],
              ["Literature and data search", "67 registered sources", "Broad novelty claims are ruled out"],
              ["New training", "None", "No verified failure target yet"],
          ], [1.7*inch, 1.75*inch, 3.2*inch]),
          PageBreak()]

story += [P("Problem Statement", "H1x"),
          P("The goal is to make AI generated engineering drawings trustworthy enough to inspect, edit and compare. The target is an object drawing such as a building frame, piece of furniture or manufactured part. Scientific contour pictures are outside the main scope unless they support the object drawing.", "Lead"),
          P("The central problem is that visual quality is not enough. An SVG may contain clean lines and readable text but still have wrong dimensions, mismatched views or a design that fails under load. A useful system must preserve both appearance and engineering meaning.", "Bodyx"),
          P("Research question", "H2x"),
          P("Can an AI system edit a detached engineering SVG, recover enough of the missing relationships to keep the drawing consistent, and attach checkable evidence to the engineering claims in the final drawing?", "Quote"),
          P("The word detached means that the SVG no longer has the original CAD feature history or associative dimension links. The system must infer relationships from visible geometry, dimensions, notes and views. If the input is ambiguous, it should state that ambiguity instead of silently choosing one interpretation.", "Bodyx"),
          P("What success requires", "H2x"),
          bullet("The requested geometry is created or edited correctly."),
          bullet("Dimensions, notes, hidden lines and different views describe the same object."),
          bullet("The chosen engineering checks use the same geometry and dimensions shown in the final drawing."),
          bullet("The result states its assumptions and does not claim more safety or certainty than the checks support."),
          bullet("A grader can reproduce the result without access to a hidden answer during generation."),
          PageBreak()]

story += [P("System Architecture", "H1x"),
          P("The architecture separates drawing generation from verification. This makes it possible to identify whether a failure comes from interpreting the drawing, changing the geometry, running the analysis or reporting the result.", "Lead"),
          architecture_table(), Spacer(1, 16),
          P("How information moves through the system", "H2x"),
          bullet("The input layer reads the source SVG, dimensions, notes, views and the requested change."),
          bullet("The interpretation layer creates a small engineering model: geometry, member or feature identities, constraints, loads, supports and assumptions."),
          bullet("The generation layer produces an edited SVG, CAD solid or selected catalog dimensions."),
          bullet("The verification layer reads the produced artifact again. It checks visible geometry and runs the appropriate engineering methods."),
          bullet("The evidence layer records the final values, pass or fail status, assumptions, raw interactions and reproducibility information."),
          P("The important design rule is that the final artifact is checked after generation. The grader does not accept a model's explanation as proof. It reads the drawing or solid and calculates the result again.", "Bodyx"),
          P("Analysis methods", "H2x"),
          table([
              ["Object or change", "Methods used or planned", "Purpose"],
              ["Building or furniture frame", "Frame FEM, stress, displacement, member buckling and mass", "Check structural behavior under stated loads"],
              ["Machined part", "Solid validity, dimensions, feature counts, volumes and local geometric probes", "Check that holes, pockets and other features exist correctly"],
              ["Sheet metal pattern", "Flat to folded geometry, surface membership and trim checks", "Check whether the flat pattern maps to the intended surface"],
              ["Multi view drawing", "Cross view geometry, notes, hidden lines and feature identity", "Check that every view represents the same edit"],
              ["Ambiguous drawing", "Feasible alternatives and constraint solving", "Show what is determined and what remains uncertain"],
          ], [1.3*inch, 2.65*inch, 2.7*inch]),
          PageBreak()]

story += [P("Work Completed", "H1x"),
          P("Structural and plate drawing pilots", "H2x"),
          P("The first object drawing pilot implemented idealized building frames and solid plates. It connected SVG geometry and dimensions to numerical analysis. Later tests added difficult curves, gears, cams, torus sections and native CAD edits. These tests helped remove false failure claims and improve the graders.", "Bodyx"),
          P("Detached SVG editing", "H2x"),
          P("A mounting panel benchmark tested edits under different visible dimensioning intentions. The starting shape could be the same while the correct hole movement differed. Astra passed all four conditions, and a handwritten rule system also passed. This showed that the fixture was useful for testing the evaluator but too easy to establish a learning advantage.", "Bodyx"),
          P("Manufacturing drawings", "H2x"),
          P("Three rolled sheet development patterns and two multi view machining plate edits were created with automatic graders. Astra passed all five. One apparent failure was traced to equivalent wording, THROUGH versus THRU, and was corrected without changing the original run records.", "Bodyx"),
          P("Released complex CAD cases", "H2x"),
          P("Two complex drawings from CADGenBench were reconstructed as valid CAD solids. Local audits passed 38 checks for one part and 11 for the other. The complete target geometry could not be scored because the private ground truth was not available and some dimensions were ambiguous. These cases are recorded as partially checked, not as full passes or failures.", "Bodyx"),
          P("Functional structural design", "H2x"),
          P("A new benchmark asked Astra to choose member sizes from a fixed catalog. Each design had to meet stress, displacement, member buckling and total mass limits under three load cases. An exhaustive search first proved that every released task had at least one valid answer. The final SVG was generated from the selected dimensions and then read back for verification.", "Bodyx"),
          PageBreak()]

story += [P("Functional Design Results", "H1x"),
          P("All six structural design tasks passed. The tasks were intentionally tight: some had only one acceptable catalog assignment near the minimum mass. The final three bay task contained 14 member choices and only two acceptable assignments among 4,782,969 combinations.", "Lead"),
          table([
              ["Task", "All assignments", "Accepted by mass cap", "Astra", "Cross entropy baseline", "Coordinate baseline"],
              ["Frame 1", "65,536", "2", "Pass", "9 of 20", "Pass"],
              ["Frame 2", "65,536", "7", "Pass", "19 of 20", "Pass"],
              ["Frame 3", "65,536", "1", "Pass", "3 of 20", "Pass"],
              ["Frame 4", "65,536", "5", "Pass", "13 of 20", "Pass"],
              ["Braced frame", "531,441", "1", "Pass", "6 of 20", "Pass"],
              ["Three bay frame", "4,782,969", "2", "Pass", "0 of 20", "Fail"],
          ], [1.15*inch, 1.05*inch, 1.0*inch, .65*inch, 1.45*inch, 1.35*inch], center_cols=(1,2,3,4,5)),
          Spacer(1, 12),
          P("Across the six tasks, the reference process checked 5,576,554 assignments. Astra used 24 successful API turns and 128,046 reported tokens. The token total includes repeated and cached context; it is not a price estimate.", "Bodyx"),
          P("The three bay result", "H2x"),
          table([
              ["Measure", "Final value", "Limit", "Result"],
              ["Mass", "6,346.380 kg", "6,409.844 kg", "Pass"],
              ["Peak stress", "99.368 MPa", "120 MPa", "Pass"],
              ["Horizontal displacement", "11.9717 mm", "12 mm", "Pass"],
              ["Vertical displacement", "1.0642 mm", "4 mm", "Pass"],
              ["Euler buckling use", "0.2383", "1.0", "Pass"],
          ], [2.25*inch, 1.45*inch, 1.45*inch, 1.05*inch], center_cols=(1,2,3)),
          P("Astra stated that its exact final assignment had not been checked by its tool. The offline grader then verified that assignment and confirmed the pass. This distinction is retained in the saved evidence.", "Small"),
          PageBreak()]

story += [P("Verification and Reproducibility", "H1x"),
          P("The project uses several checks because one method can hide mistakes in another. The most important controls are listed below.", "Lead"),
          bullet("Exhaustive feasibility checks prove that the released discrete sizing tasks have valid answers."),
          bullet("A batched FEM evaluator is compared with a separate scalar assembly and subdivided elements."),
          bullet("Closed form axial displacement and Euler buckling formulas provide analytical controls."),
          bullet("The SVG grader reads visible member widths and section rectangles instead of trusting saved metadata."),
          bullet("Raw API requests, responses, tool outputs, final answers, hashes and usage records are stored."),
          bullet("Operational errors, truncated outputs, annotation only problems and valid alternative designs are excluded from hard case claims."),
          P("Limits of the structural model", "H2x"),
          P("The frame model is linear and two dimensional. It assumes rigid joints and nodal loads. The buckling check is a member level Euler calculation with the stated effective length. The system does not check global instability, connection behavior, plastic failure, self weight, out of plane effects or building code compliance. These drawings are research artifacts, not construction approvals.", "Bodyx"),
          P("Hard case admission rule", "H2x"),
          P("A shape or design should enter the training set only after three independent completed failures survive review of the task, reference, representation and grader. The current functional benchmark contains zero admitted hard cases because every final design passed.", "Bodyx"),
          P("Current training status", "H2x"),
          P("No new training was started from these discovery cases. An earlier small CAD Editor LoRA pilot exists, but it does not prove learning for SVG drawing edits or physics based design. Training now would target examples that Astra already solves and would not answer the main research question.", "Bodyx"),
          PageBreak()]

story += [P("Literature and Dataset Foundation", "H1x"),
          P("The registry contains 67 papers, datasets, projects and documentation sources. Their review depth is recorded. Some were reviewed in full, while others were checked only through an abstract, project page or publisher excerpt. Publication does not automatically grant permission to use a dataset for training.", "Lead"),
          P("Closest prior work", "H2x"),
          table([
              ["Prior work", "What it already covers", "Effect on this project"],
              ["EngDesign", "Simulation based engineering design and structural sizing", "FEM verified sizing is not a new task idea"],
              ["StructureClaw", "Structural artifacts, numerical checks, image or DXF reconstruction and repeated trials", "Traceable engineering workflows alone are not new"],
              ["Drawing2CAD and CAD Editor", "Drawing reconstruction and instruction based CAD edits", "Generation and editing alone are not new"],
              ["Sketch to CAD intermediate representation", "Visible, inferred, assumed and missing information", "Explicit uncertainty labels alone are not new"],
              ["Planar truss documentation workflow", "Sketch interpretation, structural optimization and verified documents", "Drawing plus structural checking is already studied"],
              ["Chart2SVG and constraint SVG work", "Dependency graphs and propagated SVG edits", "Constraint linked SVG editing has prior art"],
          ], [1.5*inch, 2.45*inch, 2.7*inch]),
          P("Useful data sources", "H2x"),
          table([
              ["Source", "Possible use", "Important restriction"],
              ["CAD Editor", "Instruction and before or after CAD pairs", "Existing pilot only; preserve source lineage"],
              ["Drawing2CAD and Text2CAD", "Drawing or text aligned with CAD sequences", "Check data rights separately from code license"],
              ["SketchGraphs", "Sketch primitives and constraints", "Source copyright and terms still apply"],
              ["BenDFM", "Folded and unfolded sheet metal with process labels", "Large download; GPL declaration; not downloaded"],
              ["EPICCAD", "History, constraints, views, STEP and intent descriptions", "Access and training license still need verification"],
              ["CADGenBench", "Public drawing inputs for evaluation", "Private target geometry prevents full local scoring"],
          ], [1.5*inch, 2.35*inch, 2.8*inch]),
          PageBreak()]

story += [P("Novelty Position", "H1x"),
          P("The broad idea is not new. Existing work already combines language models with CAD, simulation, structural analysis, constraint checking, uncertainty records and iterative repair. The project should not claim that adding FEM to SVG generation is a novel contribution.", "Lead"),
          P("The strongest remaining research direction is a specific evaluation contract for detached engineering drawings. The input has lost its CAD associations. Visible dimensions and notes define how an edit should behave. Two drawings may start with identical geometry but require different correct edits because their dimensioning intent differs. When information is missing, the system should show valid alternatives and state which claims can still be verified.", "Bodyx"),
          P("Candidate contribution", "H2x"),
          bullet("A benchmark of detached engineering SVG edits with matched geometry but different visible design intent."),
          bullet("Evaluation of geometry, dimensions, notes, cross view consistency and engineering claims in one final artifact."),
          bullet("Evidence for each requested change or check: verified, ambiguous, inconsistent or unsupported."),
          bullet("Comparisons with strong models, rule based systems and classical engineering tools."),
          P("This is still a hypothesis, not an established novelty claim. The current fixtures are small and Astra passed them. A defensible paper needs a larger benchmark, a clear empirical gap and comparison with the closest systems.", "Bodyx"),
          P("What the current results do establish", "H2x"),
          P("The project now has a reproducible evaluation base and a corrected understanding of Astra's capability. Astra solved every fully scored functional design case tested under limited solver access. The result is valuable because it prevents the project from training against invented failures or making claims that the evidence does not support.", "Bodyx"),
          PageBreak()]

story += [P("Recommended Next Steps", "H1x"),
          P("The next phase should improve the benchmark before starting another training run.", "Lead"),
          table([
              ["Priority", "Action", "Completion evidence"],
              ["1", "Build 30 or more detached drawing edits across mechanical parts, furniture and simple structures", "At least three independent object families with frozen sources and references"],
              ["2", "Create matched intent pairs and missing or conflicting information variants", "Each case has documented valid alternatives or a unique answer"],
              ["3", "Use checks suited to each object", "FEM where structural behavior matters, plus geometry, kinematics, manufacturing and tolerance checks where appropriate"],
              ["4", "Run strong baselines before training", "Astra, rule based parsing, classical optimization and existing CAD systems evaluated on the same held out cases"],
              ["5", "Admit only reviewed repeatable failures", "Three independent failures with representation and grader audits"],
              ["6", "Train only after the failure set is large enough", "At least ten confirmed geometry or design failures across three families, with leakage controlled splits"],
          ], [.65*inch, 3.35*inch, 2.65*inch], center_cols=(0,)),
          P("A useful near term deliverable is a benchmark paper or technical report focused on evaluation. Training can follow if the benchmark reveals a repeatable gap. If the strongest models continue to pass, that result should guide the project toward harder inputs such as raster drawings, incomplete annotations, real multi view sheets and manufacturing constraints.", "Bodyx"),
          P("Project conclusion", "H2x"),
          P("The project has moved from a broad idea to a tested engineering drawing pipeline. The validators and evidence records are the strongest completed assets. The experiments did not find the requested Astra hard shapes, and the literature does not support a broad novelty claim. The sound path forward is to expand the detached drawing benchmark, preserve honest failure criteria and train only when a real, repeatable gap appears.", "Bodyx"),
          PageBreak()]

story += [P("Glossary", "H1x"),
          table([
              ["Term", "Simple meaning"],
              ["SVG", "A vector drawing format made from editable geometric elements and text"],
              ["CAD", "Computer aided design data used to describe parts, assemblies or drawings"],
              ["FEM", "Finite element method, a numerical way to estimate how a structure responds to loads"],
              ["Buckling", "A stability failure where a compressed member bends sideways"],
              ["Detached drawing", "A drawing that no longer has links to its original CAD model or design history"],
              ["Design intent", "The relationships that explain how geometry should change when a dimension changes"],
              ["Oracle", "A verified reference process used by the evaluator, hidden from the model during generation"],
              ["Hard case", "A valid task that repeatedly fails after the task, reference and grader have been audited"],
              ["LoRA", "A lightweight method for adapting a language model with a smaller set of trainable weights"],
          ], [1.35*inch, 5.3*inch]),
          P("Key project records", "H2x"),
          P("Functional results: cvpr2027/reports/CAD_FUNCTIONAL_DISCOVERY_20260921.md", "Small"),
          P("Extended tests: cvpr2027/reports/CAD_EXTENDED_DISCOVERY_20260921.md", "Small"),
          P("Project foundation: cvpr2027/reports/PROJECT_FOUNDATION_20260921.md", "Small"),
          P("Source registry: cvpr2027/data/cad_sources.json", "Small"),
          P("Audited functional results: cvpr2027/runs/astra-functional-sizing-20260921/audited-summary.json", "Small"),
          Spacer(1, 14),
          P("Document date 22 September 2026", "Small")]

OUT.parent.mkdir(parents=True, exist_ok=True)
ReportDoc(str(OUT)).build(story)
print(OUT)
