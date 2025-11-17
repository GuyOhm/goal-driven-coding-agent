def answer(question):
    if not isinstance(question, str):
        raise ValueError("unknown operation")

    if not question.startswith("What is"):
        raise ValueError("unknown operation")
    if not question.endswith("?"):
        raise ValueError("unknown operation")

    # Remove leading phrase and trailing question mark
    body = question[len("What is"):].strip()
    # remove trailing '?'
    if body.endswith("?"):
        body = body[:-1].strip()

    if body == "":
        raise ValueError("syntax error")

    words = body.split()
    elements = []
    i = 0
    while i < len(words):
        w = words[i]
        if w == "plus":
            elements.append("plus")
            i += 1
        elif w == "minus":
            elements.append("minus")
            i += 1
        elif w == "multiplied":
            # expect 'by' next
            if i + 1 >= len(words) or words[i + 1] != "by":
                raise ValueError("syntax error")
            elements.append("multiplied")
            i += 2
        elif w == "divided":
            if i + 1 >= len(words) or words[i + 1] != "by":
                raise ValueError("syntax error")
            elements.append("divided")
            i += 2
        else:
            # try parse number
            try:
                num = int(w)
                elements.append(num)
                i += 1
            except Exception:
                # unknown token -> unknown operation
                raise ValueError("unknown operation")

    # Validate sequence: must be number (op number)*
    if len(elements) == 0:
        raise ValueError("syntax error")

    # First must be number
    if not isinstance(elements[0], int):
        raise ValueError("syntax error")

    for idx in range(1, len(elements)):
        if idx % 2 == 1:
            # should be operator
            if not isinstance(elements[idx], str):
                raise ValueError("syntax error")
        else:
            # should be number
            if not isinstance(elements[idx], int):
                raise ValueError("syntax error")

    # If it ends with an operator (even length), it's syntax error
    if len(elements) % 2 == 0:
        raise ValueError("syntax error")

    # Evaluate left-to-right
    result = elements[0]
    idx = 1
    while idx < len(elements):
        op = elements[idx]
        num = elements[idx + 1]
        if op == "plus":
            result = result + num
        elif op == "minus":
            result = result - num
        elif op == "multiplied":
            result = result * num
        elif op == "divided":
            # use integer division with truncation toward zero
            try:
                result = int(result / num)
            except ZeroDivisionError:
                raise
        else:
            # unknown operation
            raise ValueError("unknown operation")
        idx += 2

    return result
