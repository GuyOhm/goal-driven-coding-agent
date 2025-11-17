import json


class RestAPI:
    def __init__(self, database=None):
        if database is None:
            database = {"users": []}
        self.database = database

    def _find_user(self, name):
        for user in self.database.get("users", []):
            if user.get("name") == name:
                return user
        return None

    def _user_copy(self, user):
        # return a copy suitable for output (ensure dicts and floats)
        return {
            "name": user["name"],
            "owes": dict(user.get("owes", {})),
            "owed_by": dict(user.get("owed_by", {})),
            "balance": float(user.get("balance", 0.0)),
        }

    def _recompute_balance(self, user):
        owes_total = sum(user.get("owes", {}).values())
        owed_by_total = sum(user.get("owed_by", {}).values())
        user["balance"] = owed_by_total - owes_total

    def get(self, url, payload=None):
        if url != "/users":
            return json.dumps({})
        if payload:
            data = json.loads(payload)
            names = data.get("users")
            users = []
            for name in sorted(names):
                u = self._find_user(name)
                if u:
                    users.append(self._user_copy(u))
            return json.dumps({"users": users})
        else:
            users = [self._user_copy(u) for u in sorted(self.database.get("users", []), key=lambda x: x.get("name"))]
            return json.dumps({"users": users})

    def post(self, url, payload=None):
        data = json.loads(payload) if payload else {}
        if url == "/add":
            name = data.get("user")
            # create user only if not exists
            if self._find_user(name) is None:
                user = {"name": name, "owes": {}, "owed_by": {}, "balance": 0.0}
                self.database.setdefault("users", []).append(user)
            else:
                user = self._find_user(name)
            return json.dumps(self._user_copy(user))
        elif url == "/iou":
            lender_name = data.get("lender")
            borrower_name = data.get("borrower")
            amount = float(data.get("amount", 0.0))
            lender = self._find_user(lender_name)
            borrower = self._find_user(borrower_name)
            # Initialize owes/owed_by if missing
            lender.setdefault("owes", {})
            lender.setdefault("owed_by", {})
            borrower.setdefault("owes", {})
            borrower.setdefault("owed_by", {})

            # If lender owes borrower already, reduce that debt first
            lender_owes_borrower = lender["owes"].get(borrower_name, 0.0)
            if lender_owes_borrower:
                if lender_owes_borrower > amount:
                    # reduce lender's owes to borrower
                    lender["owes"][borrower_name] = round(lender_owes_borrower - amount, 10)
                    borrower["owed_by"][lender_name] = round(lender_owes_borrower - amount, 10)
                elif lender_owes_borrower == amount:
                    # remove debt entries
                    lender["owes"].pop(borrower_name, None)
                    borrower["owed_by"].pop(lender_name, None)
                else:
                    # existing smaller than amount: remove existing and create reverse debt
                    remaining = round(amount - lender_owes_borrower, 10)
                    lender["owes"].pop(borrower_name, None)
                    borrower["owed_by"].pop(lender_name, None)
                    # borrower now owes lender remaining
                    borrower["owes"][lender_name] = round(borrower.get("owes", {}).get(lender_name, 0.0) + remaining, 10)
                    lender["owed_by"][borrower_name] = round(lender.get("owed_by", {}).get(borrower_name, 0.0) + remaining, 10)
            else:
                # normal case: borrower owes lender amount
                borrower["owes"][lender_name] = round(borrower.get("owes", {}).get(lender_name, 0.0) + amount, 10)
                lender["owed_by"][borrower_name] = round(lender.get("owed_by", {}).get(borrower_name, 0.0) + amount, 10)

            # cleanup zero entries
            for u in (lender, borrower):
                owes = {k: v for k, v in u.get("owes", {}).items() if abs(v) > 1e-9}
                owed_by = {k: v for k, v in u.get("owed_by", {}).items() if abs(v) > 1e-9}
                u["owes"] = owes
                u["owed_by"] = owed_by
                self._recompute_balance(u)

            users = [self._user_copy(self._find_user(n)) for n in sorted([lender_name, borrower_name])]
            return json.dumps({"users": users})
        else:
            return json.dumps({})
