# Структура базы данных

Проект содержит 26 таблиц:

1. `roles`;
2. `users`;
3. `password_reset_tokens`;
4. `courses`;
5. `course_enrollments`;
6. `course_modules`;
7. `lessons`;
8. `uploaded_files`;
9. `lesson_materials`;
10. `lesson_progress`;
11. `programming_tasks`;
12. `task_test_cases`;
13. `submissions`;
14. `submission_test_results`;
15. `quizzes`;
16. `quiz_questions`;
17. `quiz_options`;
18. `quiz_attempts`;
19. `quiz_answers`;
20. `achievements`;
21. `user_achievements`;
22. `feedback_requests`;
23. `feedback_messages`;
24. `notifications`;
25. `audit_logs`;
26. `system_settings`.

Основная иерархия образовательного содержимого: `courses → course_modules → lessons → programming_tasks → task_test_cases`.
