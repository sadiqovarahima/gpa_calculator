"""
Tərs GPA Kalkulyatoru
----------------------
Tələbənin hədəf ortalamaya (100 balliq sistemdə) çatmaq üçün
naməlum fənlərdən minimum neçə bal alması lazım olduğunu hesablayır.
"""

from dataclasses import dataclass
from typing import Optional


# ============================================================
# 1. DATA MODELİ
# ============================================================
# Hər fənni təsvir edən struktur.
# score = None -> bu fənn hələ naməlumdur (imtahanı yoxdur)
# score = 0-100 -> bu fənn artıq bəllidir

@dataclass
class Subject:
    name: str
    credit: float
    score: Optional[float] = None  # None = naməlum fənn


# ============================================================
# 2. BAL -> HƏRF ÇEVİRMƏ CƏDVƏLİ
# ============================================================
# Bu hədləri öz universitetinin dəqiq sisteminə görə dəyişə bilərsən.

SCORE_TO_LETTER = [
    (91, "A", 4.0),
    (81, "B", 3.0),
    (71, "C", 2.0),
    (61, "D", 1.0),
    (51, "E", 0.5),
    (0,  "F", 0.0),
]


def score_to_letter(score: float) -> tuple[str, float]:
    """Verilən bala uyğun hərf qiymətini və GPA qarşılığını qaytarır."""
    for min_score, letter, gpa in SCORE_TO_LETTER:
        if score >= min_score:
            return letter, gpa
    return "F", 0.0


# ============================================================
# 3. CARİ ORTALAMANI HESABLAYAN FUNKSİYA
# ============================================================
# Yalnız bəlli (score != None) fənləri nəzərə alaraq çəkili orta hesablayır.

def calculate_current_average(subjects: list[Subject]) -> float:
    total_points = 0.0
    total_credits = 0.0

    for s in subjects:
        if s.score is not None:
            total_points += s.score * s.credit
            total_credits += s.credit

    if total_credits == 0:
        return 0.0

    return total_points / total_credits


# ============================================================
# 4. ƏSAS FUNKSİYA — TƏRS MÜHƏNDİSLİK
# ============================================================
# Hər naməlum fənn üçün ayrıca sual verir:
# "Digər naməlumlardan minimum keçid balı fərz etsək,
#  BU fəndən neçə almalıyam ki, hədəf ortalamaya çatım?"

@dataclass
class Recommendation:
    name: str
    credit: float
    required_score: float
    required_letter: str
    gpa_equivalent: float
    feasible: bool


def reverse_engineer_score(
    subjects: list[Subject],
    target_average: float,
    min_pass_score: float = 51.0
) -> list[Recommendation]:

    total_credits = sum(s.credit for s in subjects)
    results: list[Recommendation] = []

    unknown_subjects = [s for s in subjects if s.score is None]

    for target in unknown_subjects:
        fixed_points = 0.0

        for s in subjects:
            if s.name == target.name:
                continue
            if s.score is not None:
                fixed_points += s.score * s.credit
            else:
                # digər naməlum fənlər üçün minimum keçid balını fərz edirik
                fixed_points += min_pass_score * s.credit

        # Tənliyin tərsi:
        # target_average = (fixed_points + x * credit) / total_credits
        # x = (target_average * total_credits - fixed_points) / credit
        required_score_raw = (
            (target_average * total_credits - fixed_points) / target.credit
        )

        feasible = required_score_raw <= 100
        required_score = max(0, round(required_score_raw))
        letter, gpa = score_to_letter(required_score)

        results.append(Recommendation(
            name=target.name,
            credit=target.credit,
            required_score=required_score,
            required_letter=letter if feasible else "MÜMKÜN DEYİL",
            gpa_equivalent=gpa,
            feasible=feasible,
        ))

    return results


# ============================================================
# 5. NƏTİCƏLƏRİ GÖZƏL ÇAP ETMƏK
# ============================================================

def print_report(subjects: list[Subject], target_average: float):
    current = calculate_current_average(subjects)
    print(f"\nCari ortalama (bəlli fənlərdən): {current:.1f}")
    print(f"Hədəf ortalama: {target_average}")
    print("-" * 50)

    recommendations = reverse_engineer_score(subjects, target_average)

    if not recommendations:
        print("Bütün fənlərin qiyməti artıq bəllidir.")
        return

    for r in recommendations:
        if r.feasible:
            print(
                f"{r.name} ({r.credit} kredit): "
                f"minimum {r.required_score} bal "
                f"({r.required_letter}, GPA {r.gpa_equivalent}) lazımdır."
            )
        else:
            print(
                f"{r.name} ({r.credit} kredit): "
                f"HƏDƏFƏ ÇATMAQ MÜMKÜN DEYİL (100-dən çox bal tələb olunur)."
            )


# ============================================================
# 6. TEST — NÜMUNƏ İLƏ İŞƏ SALIRIQ
# ============================================================

if __name__ == "__main__":
    subjects = [
        Subject(name="Fənn A", credit=6, score=85),
        Subject(name="Fənn B", credit=4, score=70),
        Subject(name="Fənn C", credit=8, score=None),  # naməlum
    ]

    target_average = 75

    print_report(subjects, target_average)