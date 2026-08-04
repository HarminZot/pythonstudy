from ..extensions import db
from ..models import Achievement, LessonProgress, QuizAttempt, Submission, UserAchievement
from .notification_service import notify


def evaluate_achievements(user_id):
    counts = {
        "completed_lessons": LessonProgress.query.filter_by(user_id=user_id, status="completed").count(),
        "completed_tasks": Submission.query.filter_by(user_id=user_id, status="accepted").count(),
        "perfect_quizzes": QuizAttempt.query.filter_by(user_id=user_id, status="completed", score=100).count(),
    }
    awarded = []
    for achievement in Achievement.query.filter_by(is_active=True).all():
        if achievement.condition_type not in counts:
            continue
        if counts[achievement.condition_type] < achievement.condition_value:
            continue
        exists = UserAchievement.query.filter_by(user_id=user_id, achievement_id=achievement.id).first()
        if exists:
            continue
        award = UserAchievement(user_id=user_id, achievement_id=achievement.id)
        db.session.add(award)
        notify(user_id, "Новое достижение", achievement.name, "achievement", "/student/achievements")
        awarded.append(achievement)
    return awarded
