import re
import html

def format_final_recipe(ai_text: str, goal_name: str) -> str:
    body = str(ai_text or "").replace("\r\n", "\n").strip()

    # ---- Заголовок ----
    title = None
    m = re.search(r"^\s*(?:\d+\)\s*)?\s*Название\s*:\s*(.+)$",
                  body, flags=re.IGNORECASE | re.MULTILINE)
    if m:
        title = m.group(1).strip()
        body = re.sub(r"^\s*(?:\d+\)\s*)?\s*Название\s*:.+$",
                      "", body, flags=re.IGNORECASE | re.MULTILINE)
    else:
        first_line = next((ln.strip() for ln in body.splitlines() if ln.strip()), "")
        title = first_line
        if first_line:
            body = body.replace(first_line, "", 1)

    # ---- Убрать нумерацию ----
    body = re.sub(r"(?m)^\s*\d+\)\s*", "", body)

    # ---- Списки: '-'/'*' -> '• ' ----
    body = re.sub(r"(?m)^\s*-\s+", "• ", body)
    body = re.sub(r"(?m)^\s*\*\s+", "• ", body)

    # ---- Заголовки разделов с отступами ----
    def header(h: str) -> str:
        return f"\n\n<b>{h}:</b>\n"

    body = re.sub(r"(?im)^\s*(?:\d+\)\s*)?ингредиенты\s*:\s*$",
                  header("Ингредиенты"), body)
    body = re.sub(r"(?im)^\s*(?:\d+\)\s*)?ингредиенты\s*:\s*",
                  header("Ингредиенты"), body)
    body = re.sub(r"(?im)^\s*(?:\d+\)\s*)?шаги\s*:\s*$",
                  header("Шаги"), body)
    body = re.sub(r"(?im)^\s*(?:\d+\)\s*)?шаги\s*:\s*",
                  header("Шаги"), body)
    body = re.sub(r"(?im)^\s*(?:\d+\)\s*)?кбжу.*:\s*$",
                  header("КБЖУ на порцию"), body)
    body = re.sub(r"(?im)^\s*(?:\d+\)\s*)?кбжу.*:\s*",
                  header("КБЖУ на порцию"), body)
    body = re.sub(r"(?im)^\s*(?:\d+\)\s*)?советы/?замены\s*:\s*$",
                  header("Советы/замены"), body)
    body = re.sub(r"(?im)^\s*(?:\d+\)\s*)?советы/?замены\s*:\s*",
                  header("Советы/замены"), body)

    # ---------- преобразуем КБЖУ в список ----------
    # Идея: после строки "<b>КБЖУ на порцию</b>" часто идёт всё в одну строку:
    # "Калорийность ~350 ккал; белки ~15 г; жиры ~9 г; углеводы ~35 г"
    # Ниже превращаем её в пункты "• ...".
    lines = body.splitlines()
    new_lines = []
    in_kbju = False
    converted_this_block = False

    for ln in lines:
        stripped = ln.strip()

        # вошли в секцию КБЖУ
        if stripped.startswith("<b>КБЖУ на порцию</b>"):
            in_kbju = True
            converted_this_block = False
            new_lines.append(ln)
            continue

        if in_kbju:
            # конец секции КБЖУ — пустая строка или новый жирный заголовок
            if stripped == "" or stripped.startswith("<b>"):
                in_kbju = False
                converted_this_block = False
                new_lines.append(ln)
                continue

            # первую содержательную строку КБЖУ преобразуем из "в одну строку" в пункты
            if not converted_this_block:
                # дробим по ; , . (с пробелами/без)
                parts = re.split(r"[;,.]\s*", stripped)
                parts = [p.strip(" -–—") for p in parts if p.strip()]
                if len(parts) >= 2:
                    for p in parts:
                        new_lines.append("• " + p)
                    converted_this_block = True
                    continue  # эту строку уже целиком заменили
                # если не получилось распарсить — просто добавим как есть

        new_lines.append(ln)

    body = "\n".join(new_lines)

    # ---- Итого время отдельным блоком ----
    def time_block(mo: re.Match) -> str:
        value = mo.group(1).strip()
        return f"\n\n<b>⏱ Итого время:</b> {html.escape(value)}\n"

    body = re.sub(r"(?im)^\s*(?:⏱\s*)?итого\s+время\s*:\s*(.+)$",
                  time_block, body, count=1, flags=re.MULTILINE)

    # ---- Соответствие цели -> 🎯Цель: ... ----
    def goal_block(mo: re.Match) -> str:
        explanation = mo.group(1).strip()
        head = f"\n\n<b>🎯Цель: {html.escape(goal_name)}</b>"
        return head + ("\n" + html.escape(explanation) if explanation else "")

    body = re.sub(r"(?im)^\s*(?:\d+\)\s*)?[🎯]?\s*соответствие\s+цели\s*:\s*(.+)$",
                  goal_block, body, count=1, flags=re.MULTILINE)

    # ---- Чистим пустые строки и добавляем заголовок ----
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    title_html = f"<b>{html.escape((title or '').upper())}</b>" if title else ""
    out = f"{title_html}\n\n{body}" if title_html else body
    return out.strip()
