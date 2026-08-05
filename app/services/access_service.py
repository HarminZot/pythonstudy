from ..models import LessonProgress


def ordered_published_lessons(course):
    return [
        lesson
        for module in course.modules
        for lesson in module.lessons
        if lesson.is_published
    ]


def lesson_is_unlocked(user_id, lesson):
    course = lesson.module.course
    if not course.is_sequential:
        return True
    lessons = ordered_published_lessons(course)
    try:
        lesson_index = next(index for index, item in enumerate(lessons) if item.id == lesson.id)
    except StopIteration:
        return False
    required_previous_ids = [item.id for item in lessons[:lesson_index] if item.is_required]
    if not required_previous_ids:
        return True
    completed = LessonProgress.query.filter(
        LessonProgress.user_id == user_id,
        LessonProgress.lesson_id.in_(required_previous_ids),
        LessonProgress.status == "completed",
    ).count()
    return completed == len(required_previous_ids)
