import os
from openai import OpenAI
import json
import time

MODEL_NAME = "gpt-3.5-turbo"  # Changed from gpt-4 to gpt-3.5-turbo

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def create_analysis_prompt(text, query, analysis_type=None):
    """Створення специфічних промптів на основі типу аналізу"""
    if analysis_type is None:
        return f"Проаналізуйте цей юридичний документ відповідно до запиту користувача: {query}\n\nДокумент:\n{text}"

    prompts = {
        "risks": f"Проаналізуйте потенційні ризики в цьому юридичному документі, враховуючи запит користувача: {query}\n\nДокумент:\n{text}",
        "responsibility": f"Проаналізуйте розподіл відповідальності та положення про відповідальність у цьому документі, враховуючи запит користувача: {query}\n\n{text}",
        "obligations": f"Проаналізуйте договірні зобов'язання, терміни та зобов'язання в цьому документі, враховуючи запит користувача: {query}\n\n{text}",
        "compliance": f"Проаналізуйте відповідність цього документа чинному законодавству України, враховуючи запит користувача: {query}\n\n{text}",
        "financial": f"Проаналізуйте фінансові умови та зобов'язання в цьому документі, враховуючи запит користувача: {query}\n\n{text}"
    }
    return prompts.get(analysis_type, "")

def get_analysis(prompt, max_retries=3, timeout=60):
    """Отримання аналізу від OpenAI API з повторними спробами та таймаутом"""
    # Обмежуємо розмір тексту до ~4000 символів (приблизно 1000 токенів)
    max_text_length = 4000
    if len(prompt) > max_text_length:
        # Якщо текст завеликий, беремо перші 4000 символів
        prompt = prompt[:max_text_length] + "\n[Текст було скорочено через обмеження розміру...]"

    for attempt in range(max_retries):
        try:
            print(f"Спроба {attempt + 1} з {max_retries}")
            print(f"Розмір промпту: {len(prompt)} символів")
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "Ви експерт з аналізу юридичних документів. Надайте чіткий, структурований аналіз з ключовими пунктами та рекомендаціями українською мовою."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000,
                timeout=timeout
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            print(f"Помилка при спробі {attempt + 1}: {error_msg}")

            if "authentication" in error_msg.lower():
                return "Помилка автентифікації API ключа. Будь ласка, перевірте налаштування."
            elif "timeout" in error_msg.lower():
                if attempt < max_retries - 1:
                    print(f"Таймаут, очікування перед повторною спробою...")
                    time.sleep(2 ** attempt)
                    continue
                return "Перевищено час очікування відповіді від API"
            elif attempt == max_retries - 1:
                return f"Помилка під час аналізу: {error_msg}"

            time.sleep(2 ** attempt)
    return "Не вдалося отримати аналіз після кількох спроб"

def analyze_document(text, query, selected_types=None, progress_callback=None):
    """
    Аналіз документа за запитом користувача та вибраними типами аналізу (якщо вказані)
    """
    if not query:
        raise ValueError("Необхідно вказати запит для аналізу")

    if progress_callback:
        progress_callback(0.0, "Початок аналізу...")

    try:
        results = {}

        if selected_types is None or len(selected_types) == 0:
            # Аналіз тільки за запитом користувача
            if progress_callback:
                progress_callback(0.3, "Виконується загальний аналіз за запитом...")

            result = get_analysis(create_analysis_prompt(text, query))

            if "Помилка" in result:
                raise Exception(result)

            results["general"] = result
        else:
            # Аналіз за запитом та вибраними типами
            total_steps = len(selected_types)
            current_step = 0

            for analysis_type in selected_types:
                if progress_callback:
                    progress_callback(current_step / total_steps, f"Виконується {analysis_type} аналіз...")

                analysis_prompt = create_analysis_prompt(text, query, analysis_type)
                result = get_analysis(analysis_prompt)

                if "Помилка" in result:
                    raise Exception(result)

                results[analysis_type] = result
                current_step += 1

        if progress_callback:
            progress_callback(1.0, "Аналіз успішно завершено!")

        return results

    except Exception as e:
        error_msg = str(e)
        print(f"Критична помилка: {error_msg}")
        if progress_callback:
            progress_callback(1.0, f"Помилка: {error_msg}")
        return {"error": f"Виникла помилка під час аналізу: {error_msg}"}