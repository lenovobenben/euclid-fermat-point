"""Build and check the geometry used by the Fermat-point animation in SageMath."""

import hashlib
import json
from itertools import permutations
from pathlib import Path

from sage.all import AA, QQ
from sage.version import version


HERE = Path(__file__).resolve().parent


def add(first, second):
    return tuple(x + y for x, y in zip(first, second))


def subtract(first, second):
    return tuple(x - y for x, y in zip(first, second))


def scale(factor, point):
    return tuple(factor * value for value in point)


def dot(first, second):
    return sum(x * y for x, y in zip(first, second))


def cross(first, second):
    return first[0] * second[1] - first[1] * second[0]


def length(vector):
    return dot(vector, vector).sqrt()


def rotate_clockwise(point, center):
    x, y = subtract(point, center)
    root = AA(3).sqrt()
    return add(center, ((x + root * y) / 2, (y - root * x) / 2))


def circle_intersections(first, first_radius_squared, second, second_radius_squared):
    direction = subtract(second, first)
    norm_squared = dot(direction, direction)
    if norm_squared == 0:
        raise ValueError("circle centers must be different")
    fraction = (norm_squared + first_radius_squared - second_radius_squared) / (2 * norm_squared)
    foot = add(first, scale(fraction, direction))
    height_squared = first_radius_squared / norm_squared - fraction ** 2
    if height_squared <= 0:
        raise ValueError("two distinct circle intersections are required")
    normal = (-direction[1], direction[0])
    offset = scale(height_squared.sqrt(), normal)
    points = (add(foot, offset), subtract(foot, offset))
    for point in points:
        assert dot(subtract(point, first), subtract(point, first)) == first_radius_squared
        assert dot(subtract(point, second), subtract(point, second)) == second_radius_squared
    return points


def outside_equilateral(first, second, third):
    direction = subtract(second, first)
    radius_squared = dot(direction, direction)
    candidates = circle_intersections(first, radius_squared, second, radius_squared)
    third_side = cross(direction, subtract(third, first))
    selected = [point for point in candidates
                if third_side * cross(direction, subtract(point, first)) < 0]
    assert len(selected) == 1
    return selected[0], candidates


def angle_comparison(vertex, first, second):
    ray = subtract(second, vertex)
    radius = length(subtract(first, vertex))
    target = add(vertex, scale(radius / length(ray), ray))
    outside, _ = outside_equilateral(vertex, first, second)
    opposite = subtract(scale(2, vertex), outside)
    difference = dot(subtract(target, first), subtract(target, first)) - dot(
        subtract(opposite, first), subtract(opposite, first))
    direction_first = subtract(first, vertex)
    cosine = dot(direction_first, ray) / (radius * length(ray))
    comparison = difference.sign()
    assert comparison == (-1 - 2 * cosine).sign()
    return int(comparison), {"T": target, "H": opposite, "K": outside}


def line_intersection(first, second, third, fourth):
    direction = subtract(second, first)
    other = subtract(fourth, third)
    determinant = cross(direction, other)
    if determinant == 0:
        raise ValueError("the two construction lines must have a unique intersection")
    fraction = cross(subtract(third, first), other) / determinant
    return add(first, scale(fraction, direction))


def construct(coordinates):
    points = [tuple(AA(value) for value in point) for point in coordinates]
    if len(points) != 3 or cross(subtract(points[1], points[0]), subtract(points[2], points[0])) == 0:
        raise ValueError("three noncollinear points are required")
    comparisons = [angle_comparison(points[index], points[(index + 1) % 3],
                                    points[(index + 2) % 3])[0] for index in range(3)]
    for index, comparison in enumerate(comparisons):
        if comparison >= 0:
            return {"P": points[index], "branch": "vertex", "angles": comparisons}
    a, b, c = points
    d, _ = outside_equilateral(a, b, c)
    e, _ = outside_equilateral(b, c, a)
    p = line_intersection(c, d, a, e)
    directions = [subtract(point, p) for point in points]
    for index in range(3):
        first, second = directions[index], directions[(index + 1) % 3]
        inner = dot(first, second)
        assert inner < 0 and 4 * inner ** 2 == dot(first, first) * dot(second, second)
    orientation = cross(subtract(b, a), subtract(c, a))
    assert all(orientation * cross(subtract(points[(index + 1) % 3], points[index]),
                                   subtract(p, points[index])) > 0 for index in range(3))
    assert dot(subtract(d, c), subtract(d, c)) == dot(subtract(e, a), subtract(e, a))
    for first, last in ((c, d), (a, e)):
        assert dot(subtract(p, first), subtract(p, last)) < 0
    return {"P": p, "D": d, "E": e, "branch": "interior", "angles": comparisons}


def display_points(points):
    return {name: [float(value) for value in point] for name, point in points.items()}


def run():
    root = AA(3).sqrt()
    main = ((0, 0), (4, 0), (1, 3))
    result = construct(main)
    p = result["P"]
    assert p == ((10 + 4 * root) / 13, (24 - 6 * root) / 13)
    a, b, c = (tuple(AA(value) for value in point) for point in main)
    d, d_candidates = outside_equilateral(a, b, c)
    e, e_candidates = outside_equilateral(b, c, a)
    p_prime = rotate_clockwise(p, a)
    assert cross(subtract(p_prime, c), subtract(d, c)) == 0
    assert dot(subtract(p_prime, p), subtract(d, p_prime)) > 0
    assert length(subtract(p_prime, p)) == length(subtract(p, a))
    assert length(subtract(d, p_prime)) == length(subtract(p, b))
    assert length(subtract(d, c)) == (22 + 12 * root).sqrt()
    assert sum(length(subtract(point, p)) for point in (a, b, c)) == length(subtract(d, c))
    q = (AA(14) / 5, AA(8) / 5)
    q_prime = rotate_clockwise(q, a)
    assert length(subtract(q_prime, q)) == length(subtract(q, a))
    assert length(subtract(q_prime, d)) == length(subtract(q, b))
    assert sum(length(subtract(q, point)) for point in (a, b, c)) > length(subtract(d, c))

    epsilon = QQ(1) / 10 ** 30
    examples = {
        "main": main,
        "equilateral": ((0, 0), (2, 0), (1, root)),
        "isosceles": ((-2, 0), (2, 0), (0, 3)),
        "right": ((0, 0), (3, 0), (0, 2)),
        "obtuse_below_120": ((0, 0), (3, 0), (-QQ(1) / 2, 2)),
        "boundary": ((0, 0), (3, 0), (-1, root)),
        "large": ((0, 0), (3, 0), (-root, 1)),
        "near_below": ((0, 0), (3, 0), (-1 + epsilon, root)),
        "near_above": ((0, 0), (3, 0), (-1 - epsilon, root)),
    }
    replays = 0
    for name, coordinates in examples.items():
        print("Checking " + name, flush=True)
        reference = construct(coordinates)
        expected = "vertex" if name in ("boundary", "large", "near_above") else "interior"
        assert reference["branch"] == expected
        permutations_to_check = permutations(coordinates) if name == "main" else (coordinates,)
        for permuted in permutations_to_check:
            for reflected in (False, True):
                transformed = [(AA(-2 if reflected else 2) * x + QQ(1) / 7,
                                AA(2) * y - QQ(2) / 5) for x, y in permuted]
                replay = construct(transformed)
                assert replay["P"] == (AA(-2 if reflected else 2) * reference["P"][0] + QQ(1) / 7,
                                        2 * reference["P"][1] - QQ(2) / 5)
                assert replay["branch"] == reference["branch"]
                replays += 1

    threshold = angle_comparison(a, b, c)[1]
    points = {"A": a, "B": b, "C": c, "D": d, "E": e, "P": p,
              "Pprime": p_prime, "Q": q, "Qprime": q_prime, **threshold}
    points["Dother"] = next(point for point in d_candidates if point != d)
    points["Eother"] = next(point for point in e_candidates if point != e)
    payload = {
        "sage_version": version,
        "arithmetic": "SageMath AA, exact comparisons before display conversion",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "verified": {"construction_and_angles": True, "strict_interior": True,
                     "rotation_lengths": True, "equality_order": True,
                     "boundary_and_large_angles": True},
        "checked_replays": replays,
        "checked_examples": list(examples),
        "points": display_points(points),
        "angles": result["angles"],
        "boundary": display_points(dict(zip("ABC", examples["boundary"]))),
        "large": display_points(dict(zip("ABC", examples["large"]))),
        "minimum": float((22 + 12 * root).sqrt()),
    }
    output = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (HERE / "geometry.json").write_text(output, encoding="utf-8")
    (HERE / "geometry.sha256").write_text(hashlib.sha256(output.encode("utf-8")).hexdigest() + "\n",
                                          encoding="ascii")
    print(json.dumps({"valid": True, "checked_replays": replays,
                      "point": payload["points"]["P"], "minimum": payload["minimum"]}, indent=2))


if __name__ == "__main__":
    run()
