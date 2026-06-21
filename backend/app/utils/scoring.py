from app.models.form_question import FormQuestion
from app.models.form_question_option import FormQuestionOption


def calculate_option_score(question: FormQuestion, option: FormQuestionOption) -> float | None:
    if option.score is None:
        return None
    score = option.score
    if question.is_reverse_scored:
        active_scores = [
            current_option.score
            for current_option in question.options
            if current_option.deleted_at is None and current_option.score is not None
        ]
        if len(active_scores) >= 2:
            score = max(active_scores) + min(active_scores) - score
    return score


def calculate_multiple_choice_score(question: FormQuestion, options: list[FormQuestionOption]) -> float | None:
    scores = [calculate_option_score(question, option) for option in options]
    valid_scores = [score for score in scores if score is not None]
    if not valid_scores:
        return None
    return float(sum(valid_scores))
