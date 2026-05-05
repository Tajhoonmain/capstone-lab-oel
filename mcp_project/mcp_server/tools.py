def check_exam_schedule(course_code: str):
    """
    Check exam timing for a course.
    """
    exam_db = {"AI407": "Monday 2:30 PM", "CS101": "Tuesday 9:00 AM", "SE302": "Wednesday 11:00 AM"}

    return {"course": course_code, "exam_time": exam_db.get(course_code, "Exam not scheduled")}


def calculate_gpa(grades: list):
    """
    Calculate GPA from a list of letter grades.
    """
    grade_points = {"A": 4, "B": 3, "C": 2, "D": 1, "F": 0}

    if not grades:
        return {"gpa": 0.0}

    total = 0
    for g in grades:
        total += grade_points.get(g.upper(), 0)

    gpa = total / len(grades)

    return {"gpa": round(gpa, 2)}
