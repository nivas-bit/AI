import re

class KnowledgeBase:
    def __init__(self):
        self.facts = set()
        self.rules = []

    def add_fact(self, fact):
        self.facts.add(fact)

    def add_rule(self, head, body, label=None):
        self.rules.append({"head": head, "body": body, "label": label})

def substitute(expr, subs):
    for var, val in subs.items():
        expr = re.sub(r'\b' + var + r'\b', val, expr)
    return expr

def extract_predicate(expr):
    m = re.match(r'(\w+)\(([^()]*)\)', expr)
    if not m:
        return None, []
    pred, args = m.groups()
    args = [a.strip() for a in args.split(',') if a.strip()]
    return pred, args

def unify(pattern, fact):
    p_pred, p_args = extract_predicate(pattern)
    f_pred, f_args = extract_predicate(fact)
    if p_pred != f_pred or len(p_args) != len(f_args):
        return None
    subs = {}
    for pa, fa in zip(p_args, f_args):
        if pa[0].islower():
            if pa in subs:
                if subs[pa] != fa:
                    return None
            else:
                subs[pa] = fa
        elif pa != fa:
            return None
    return subs

def forward_chain(kb, query):
    derived = True
    steps = []
    while derived:
        derived = False
        for rule in kb.rules:
            body = rule["body"]
            head = rule["head"]
            label = rule["label"]

            matches = [{}]  
            for cond in body:
                new_matches = []
                for m in matches:
                    for fact in kb.facts:
                        subs = unify(cond, substitute(fact, m))
                        if subs is not None:
                            combined = {**m, **subs}
                            consistent = True
                            for k in combined:
                                if k in m and m[k] != combined[k]:
                                    consistent = False
                                    break
                            if consistent:
                                new_matches.append(combined)
                matches = new_matches

            for subs in matches:
                new_fact = substitute(head, subs)
                if new_fact not in kb.facts:
                    kb.facts.add(new_fact)
                    derived = True
                    steps.append({
                        "rule": label,
                        "substitution": subs,
                        "premises": [substitute(c, subs) for c in body],
                        "derived": new_fact
                    })
                    print(f"Derived: {new_fact} by rule {label} with substitution {subs}")
    return steps

def print_proof(query, steps):
    derived_by = {step["derived"]: step for step in steps}

    def print_tree(goal, indent=""):
        if goal not in derived_by:
            print(f"{indent}- {goal}")
        else:
            step = derived_by[goal]
            print(f"{indent}- {goal}  [derived by: {step['rule']}]")
            for p in step["premises"]:
                print_tree(p, indent + "  ")

    print(f"\nProof tree for query '{query}':")
    print_tree(query)

# -------------------------
# Create knowledge base
# -------------------------
kb = KnowledgeBase()


kb.add_fact("Owns(A, t1)")
kb.add_fact("Missile(t1)")
kb.add_fact("American(Robert)")
kb.add_fact("Enemy(A, America)")

kb.add_rule("Criminal(p)", ["American(p)", "Weapon(q)", "Sells(p, q, r)", "Hostile(r)"], label="R_crime")
kb.add_rule("Sells(Robert, x, A)", ["Missile(x)", "Owns(A, x)"], label="R_sells_by_robert")
kb.add_rule("Weapon(x)", ["Missile(x)"], label="R_missile_weapon")
kb.add_rule("Hostile(x)", ["Enemy(x, America)"], label="R_enemy_hostile")

query = "Criminal(Robert)"

steps = forward_chain(kb, query)

print("\n=== Knowledge Base Facts after Forward Chaining ===")
for f in sorted(kb.facts):
    print(" -", f)

print("\nDerivation steps:")
for i, step in enumerate(steps, 1):
    print(f"Step {i}: rule {step['rule']}")
    print("  substitution:", step["substitution"])
    print("  premises used:")
    for p in step["premises"]:
        print("   -", p)
    print("  derived:", step["derived"], "\n")

print("=== Query Result ===")
if query in kb.facts:
    print(f"Query '{query}' is TRUE (derived)")
else:
    print(f"Query '{query}' could NOT be derived")

print_proof(query, steps)
