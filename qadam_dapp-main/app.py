from flask import Flask, request, render_template, Response, jsonify
import os
import json
import requests
from collections import defaultdict
import statistics

app = Flask(__name__, template_folder='templates')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/career')
def career():
    return render_template('career.html')


@app.route('/career/predict', methods=['POST'])
def predict():
    data = request.get_json()
    skills = data.get("skills", "")
    interests = data.get("interests", "")

    # Заглушка для тестов без OpenAI
    fake_result = {
        "result": (
            "1. **Программист** - 92% совпадение\n"
            "   • Что изучить: Python, Git, SQL\n"
            "   • Перспективы: высокий спрос на рынке\n\n"
            "2. **Системный администратор** - 80% совпадение\n"
            "   • Что изучить: Linux, сетевые технологии\n"
            "   • Перспективы: стабильная занятость\n\n"
            "Дополнительно, по интересам:\n"
            "1. **Графический дизайнер** - 75%\n"
            "   • Что изучить: Photoshop, Figma\n"
            "   • Перспективы: удалённая работа"
        )
    }
    return Response(json.dumps(fake_result, ensure_ascii=False), mimetype="application/json")


@app.route('/career/relevance', methods=['POST'])
def relevance():
    data = request.get_json()
    professions = data.get("professions", [])
    area_id = data.get("area_id", 40)

    try:
        result = []
        for profession in professions:
            url = "https://api.hh.ru/vacancies"
            params = {
                "text": profession,
                "area": area_id,
                "per_page": 100,
                "period": 30
            }
            response = requests.get(url, params=params)
            data = response.json()
            vacancies = data.get("items", [])

            salaries = []
            skills_counter = defaultdict(int)

            for v in vacancies:
                salary = v.get("salary")
                if salary and salary.get("from") and salary.get("currency") == "KZT":
                    salaries.append(salary["from"])
                if v.get("key_skills"):
                    for skill in v["key_skills"]:
                        skills_counter[skill["name"].lower()] += 1

            top_skills = sorted(skills_counter.items(), key=lambda x: x[1], reverse=True)[:5]
            avg_salary = int(statistics.mean(salaries)) if salaries else None
            median_salary = int(statistics.median(salaries)) if salaries else None

            params["period"] = 60
            prev_month_response = requests.get(url, params=params)
            prev_month_data = prev_month_response.json()
            prev_month_count = prev_month_data.get("found", 0)
            current_count = data.get("found", 0)

            trend = ""
            if current_count > prev_month_count:
                trend = f"↑ {round((current_count - prev_month_count) / prev_month_count * 100)}%"
            elif current_count < prev_month_count:
                trend = f"↓ {round((prev_month_count - current_count) / prev_month_count * 100)}%"
            else:
                trend = "→ 0%"

            result.append({
                "profession": profession,
                "vacancy_count": current_count,
                "average_salary": avg_salary,
                "median_salary": median_salary,
                "trend": trend,
                "top_skills": [skill[0] for skill in top_skills],
                "search_url": f"https://hh.kz/search/vacancy?text={profession.replace(' ', '+')}&area={area_id}"
            })

        return Response(json.dumps(result, ensure_ascii=False), mimetype="application/json")

    except Exception as e:
        return Response(json.dumps({"error": str(e)}, ensure_ascii=False), mimetype="application/json")


@app.route("/ai-tree")
def ai_tree():
    return render_template("ai-tree.html")


@app.route("/about")
def about():
    return render_template("o_nas.html")


@app.route("/ai-tree/api/node", methods=["POST"])
def generate_node():
    # Возвращаем фейковый вопрос и ответы
    return jsonify({
        "question": "Что тебе больше по душе?",
        "options": ["Работа руками", "Работа с техникой"]
    })


@app.route("/ai-tree/api/result", methods=["POST"])
def generate_result():
    # Возвращаем фейковый результат
    result = (
        "Профессия: Электрик\n"
        "Ты выбрал направления, связанные с техникой и ручным трудом. Профессия электрика подходит, "
        "поскольку она востребована, позволяет работать с оборудованием и требует аккуратности."
    )
    return jsonify({"profession": result})


@app.route("/ai-tree/api/vacancies", methods=["POST"])
def get_vacancies():
    data = request.get_json()
    profession = data.get("profession", "")
    url = "https://api.hh.kz/vacancies"
    params = {
        "text": profession,
        "area": 159,
        "per_page": 5
    }
    r = requests.get(url, params=params, timeout=10)
    res = r.json()
    vacancies = []
    for v in res.get('items', []):
        salary = v.get("salary")
        salary_str = None
        if salary:
            frm = salary.get("from") or ""
            to = salary.get("to") or ""
            cur = salary.get("currency") or ""
            salary_str = f"{frm}–{to} {cur}".replace("– ", "").strip()
        vacancies.append({
            "name": v.get("name"),
            "company": v.get("employer", {}).get("name"),
            "url": v.get("alternate_url"),
            "salary": salary_str
        })
    return jsonify({"vacancies": vacancies})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
