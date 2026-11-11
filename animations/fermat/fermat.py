"""A short construction of the interior Fermat point with a rotation proof."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from manim import (
    Arc, Create, DashedLine, Dot, FadeIn, FadeOut, Line, Rotate,
    Scene, Text, Transform, VGroup, config,
)


HERE = Path(__file__).resolve().parent
FONT = "Noto Sans CJK SC"
BACKGROUND = "#07101F"
FOREGROUND = "#E8F0F7"
MUTED = "#8397A8"
INPUT = "#F45BFF"
CURRENT = "#FFC857"
AUXILIARY = "#8AC6D9"
RESULT = "#5DE2A5"
OFFSETS = {
    "A": (-0.23, -0.23), "B": (0.24, -0.20), "C": (-0.18, 0.25),
    "D": (0.22, -0.20), "E": (0.22, 0.22), "P": (0.18, -0.19),
}


def load_geometry():
    raw = (HERE / "geometry.json").read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != (HERE / "geometry.sha256").read_text("ascii").strip():
        raise ArithmeticError("animation geometry digest mismatch")
    data = json.loads(raw)
    source = (HERE / "export_geometry.py").read_bytes()
    if hashlib.sha256(source).hexdigest() != data["source_sha256"]:
        raise ArithmeticError("regenerate geometry after changing the exact geometry source")
    if not all(data["verified"].values()) or data["angles"] != [-1, -1, -1]:
        raise ArithmeticError("the interior example must pass its exact checks")
    return data, digest


@dataclass(frozen=True)
class View:
    center: tuple
    offset: tuple
    scale: float

    def at(self, point):
        result = (np.array(point) - self.center) * self.scale + self.offset
        return np.array([result[0], result[1], 0.0])


class FermatPoint(Scene):
    def text(self, content, size=24, color=FOREGROUND, width=4.7):
        result = Text(content, font=FONT, font_size=size, color=color)
        if result.width > width:
            result.scale_to_fit_width(width)
        return result

    def stage(self, title, caption, color=CURRENT):
        self.sections.append({"title": title, "start_seconds": round(float(self.time), 6)})
        replacement = self.text(caption, 25, color, 12.7).move_to([0, -3.48, 0])
        if hasattr(self, "caption_object"):
            self.remove(self.caption_object)
        self.caption_object = replacement
        self.add(replacement)

    def formula(self, lines, color=FOREGROUND):
        replacement = VGroup(*[
            self.text(line, 28, color).move_to([4.0, 0.6 - index * 0.85, 0])
            for index, line in enumerate(lines)
        ])
        if hasattr(self, "formula_object"):
            self.play(FadeOut(self.formula_object), FadeIn(replacement), run_time=0.35)
        else:
            self.play(FadeIn(replacement), run_time=0.35)
        self.formula_object = replacement

    def point(self, point, label, view, color=INPUT, offset=None):
        at = view.at(point)
        dot = Dot(at, radius=0.043, color=color).set_z_index(5)
        shift = OFFSETS.get(label, (0.23, 0.20)) if offset is None else offset
        tag = self.text(label, 22, color).move_to(at + np.array([*shift, 0])).set_z_index(6)
        return VGroup(dot, tag)

    def segment(self, first, second, view, color=AUXILIARY, width=1.6, opacity=1):
        return Line(view.at(first), view.at(second), color=color, stroke_width=width,
                    stroke_opacity=opacity)

    def compass_arc(self, center, through, intersection, view):
        direction = np.array(intersection) - center
        angle = np.arctan2(direction[1], direction[0])
        radius = np.linalg.norm(np.array(through) - center) * view.scale
        return Arc(radius=radius, start_angle=angle - 0.14, angle=0.28,
                   color=CURRENT, stroke_width=1.5).shift(view.at(center))

    def triangle(self, view, extra=()):
        points = self.points
        result = VGroup(*[
            self.segment(points[first], points[second], view, INPUT, opacity=0.65)
            for first, second in ("AB", "BC", "CA")
        ])
        result.add(*[self.point(points[name], name, view) for name in "ABC"])
        result.add(*[self.point(points[name], name, view, RESULT) for name in extra])
        return result

    def clear_diagram(self):
        preserved = (self.chrome, self.formula_object, self.caption_object)
        self.remove(*[item for item in list(self.mobjects) if item not in preserved])

    def construct(self):
        config.background_color = BACKGROUND
        self.data, self.geometry_hash = load_geometry()
        self.points = {name: np.array(point) for name, point in self.data["points"].items()}
        self.sections = []
        title = self.text("费马点的尺规构造", 32, width=9.5)
        title.move_to([-6.35, 3.47, 0], aligned_edge=np.array([-1, 0, 0]))
        condition = self.text("三个内角均小于 120°", 20, MUTED)
        condition.move_to([4.7, 3.47, 0])
        self.chrome = VGroup(title, condition,
                            Line([-6.5, 3.03, 0], [6.5, 3.03, 0], color=MUTED, stroke_width=0.6))
        self.add(self.chrome)
        self.view = View((2.3, 0.2), (-2.6, -0.05), 0.65)
        self.stage("给定三点", "求 PA + PB + PC 最小的点 P")
        self.play(FadeIn(self.triangle(self.view)), run_time=0.8)
        self.formula(["PA + PB + PC → 最小"])
        self.wait(2)
        self.equilateral("A", "B", "D")
        self.equilateral("B", "C", "E")
        self.intersection()
        self.rotation_proof()
        self.finish()
        if not config.dry_run and config.write_to_movie:
            self.write_timeline()

    def equilateral(self, first, second, apex):
        points, view = self.points, self.view
        self.stage("外作等边三角形 " + first + second + apex,
                   "在 " + first + second + " 外侧作等边三角形 " + first + second + apex)
        self.formula([first + apex + " = " + second + apex + " = " + first + second], AUXILIARY)
        arcs = VGroup(self.compass_arc(points[first], points[second], points[apex], view),
                      self.compass_arc(points[second], points[first], points[apex], view))
        self.play(Create(arcs[0]), run_time=0.9)
        self.play(Create(arcs[1]), run_time=0.9)
        self.play(FadeIn(self.point(points[apex], apex, view, RESULT)), run_time=0.4)
        edges = VGroup(self.segment(points[first], points[apex], view),
                       self.segment(points[second], points[apex], view))
        self.play(Create(edges), run_time=0.9)
        self.wait(1.5)
        self.play(FadeOut(arcs), run_time=0.35)

    def angle_marks(self, view):
        points, result = self.points, VGroup()
        for first, second in ("AB", "BC", "CA"):
            start = np.arctan2(*(points[first] - points["P"])[::-1])
            end = np.arctan2(*(points[second] - points["P"])[::-1])
            sweep = (end - start) % (2 * np.pi)
            assert abs(sweep - 2 * np.pi / 3) < 1e-10
            arc = Arc(radius=0.34, start_angle=start, angle=sweep,
                      color=RESULT, stroke_width=1.4).shift(view.at(points["P"]))
            middle = start + sweep / 2
            label = self.text("120°", 18, RESULT).move_to(
                view.at(points["P"]) + 0.59 * np.array([np.cos(middle), np.sin(middle), 0]))
            result.add(arc, label)
        return result

    def intersection(self):
        points, view = self.points, self.view
        self.stage("两线交于 P", "连接 CD、AE，交于 P")
        self.formula(["P = CD ∩ AE"], RESULT)
        for first, second in ("CD", "AE"):
            self.play(Create(self.segment(points[first], points[second], view, CURRENT, 2)), run_time=0.9)
        self.play(FadeIn(self.point(points["P"], "P", view, RESULT)), run_time=0.4)
        self.wait(1.8)
        self.stage("三个 120°", "三组夹角均为 120°")
        radii = VGroup(*[self.segment(points["P"], points[name], view, RESULT, 2.2) for name in "ABC"])
        self.play(Create(radii), Create(self.angle_marks(view)), run_time=1)
        self.wait(2.5)
        self.clear_diagram()

    def rotation_proof(self):
        points = self.points
        view = View((2, 0), (-2.7, 0), 0.78)
        self.stage("旋转 60°", "将 Q 绕 A 旋转 60° 得 Q′，B 同时转到 D")
        self.formula(["QQ′ = QA", "Q′D = QB"], AUXILIARY)
        self.play(FadeIn(self.triangle(view, ("D",))), run_time=0.5)
        q = self.point(points["Q"], "Q", view, CURRENT)
        self.play(FadeIn(q), run_time=0.35)
        moving = Dot(view.at(points["Q"]), radius=0.043, color=CURRENT)
        self.add(moving)
        self.play(Rotate(moving, angle=-np.pi / 3, about_point=view.at(points["A"])), run_time=1.3)
        self.remove(moving)
        q_prime = self.point(points["Qprime"], "Q′", view, CURRENT, (0.25, -0.08))
        self.play(FadeIn(q_prime), run_time=0.35)
        guides = VGroup(*[DashedLine(view.at(points["A"]), view.at(points[name]), color=MUTED,
                                     stroke_width=1.2, dash_length=0.08) for name in ("Q", "Qprime")])
        self.play(Create(guides), run_time=0.5)
        path = VGroup(self.segment(points["C"], points["Q"], view, AUXILIARY, 2.6),
                      self.segment(points["Q"], points["Qprime"], view, INPUT, 2.6),
                      self.segment(points["Qprime"], points["D"], view, CURRENT, 2.6))
        self.play(Create(path), run_time=0.9)
        self.wait(1.8)
        self.stage("折线下界", "折线 C—Q—Q′—D 的长度至少为 CD")
        self.formula(["QA + QB + QC ≥ CD"])
        self.wait(2.5)
        self.play(FadeOut(guides), run_time=0.3)
        self.stage("达到最小值", "Q 移到 P 时，折线伸直，达到最小值", RESULT)
        straight = VGroup(self.segment(points["C"], points["P"], view, AUXILIARY, 2.8),
                          self.segment(points["P"], points["Pprime"], view, INPUT, 2.8),
                          self.segment(points["Pprime"], points["D"], view, CURRENT, 2.8))
        self.play(Transform(q, self.point(points["P"], "P", view, RESULT, (-0.26, 0.13))),
                  Transform(q_prime, self.point(points["Pprime"], "P′", view, RESULT, (-0.30, -0.08))),
                  Transform(path, straight), run_time=2)
        self.formula(["PA + PB + PC = CD"], RESULT)
        self.wait(2.5)
        self.clear_diagram()

    def finish(self):
        points, view = self.points, self.view
        self.stage("费马点已作成", "P 就是所求的费马点", RESULT)
        diagram = self.triangle(view, ("D", "E", "P"))
        for first, second in ("AD", "BD", "BE", "CE", "CD", "AE"):
            diagram.add(self.segment(points[first], points[second], view, AUXILIARY, opacity=0.38))
        diagram.add(*[self.segment(points["P"], points[name], view, RESULT, 2.2) for name in "ABC"])
        diagram.add(self.angle_marks(view))
        self.play(FadeIn(diagram), run_time=0.6)
        self.formula(["PA + PB + PC 最小"], RESULT)
        self.wait(3)

    def write_timeline(self):
        movie = Path(self.renderer.file_writer.movie_file_path)
        report = {
            "scene": type(self).__name__, "movie_file": movie.name,
            "geometry_sha256": self.geometry_hash,
            "animation_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "resolution": [config.pixel_width, config.pixel_height],
            "frame_rate": config.frame_rate,
            "duration_seconds": round(float(self.time), 6),
            "sections": self.sections,
        }
        movie.with_suffix(".timeline.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
