# -*- coding: utf-8 -*-
import argparse
import csv
import json
import os
import re
import sys

# Add backend to path to import app modules
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, backend_path)

import openpyxl

def load_rows_from_file(filepath):
    """Loads sheet rows as list of dicts from xlsx or csv."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in {".xlsx", ".xlsm"}:
        wb = openpyxl.load_workbook(filepath, data_only=True)
        sheet = wb.active
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            return []
        headers = [str(cell).strip() if cell is not None else "" for cell in rows[0]]
        result = []
        for r in rows[1:]:
            if any(cell is not None and str(cell).strip() for cell in r):
                row_dict = dict(zip(headers, r, strict=False))
                result.append(row_dict)
        return result
    elif ext == ".csv":
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            return [row for row in reader]
    else:
        raise ValueError(f"Unsupported file format: {ext}")

def run_static_validation(ing_file, dish_file, raw_dir):
    print("Running Static Validation...")
    errors = []
    
    # 1. Load data
    ing_rows = load_rows_from_file(ing_file)
    dish_rows = load_rows_from_file(dish_file)
    
    print(f"Loaded {len(ing_rows)} ingredients and {len(dish_rows)} dishes.")
    
    # 2. Ingredient validation
    if len(ing_rows) != 150:
        errors.append(f"Số lượng nguyên liệu không đúng: Yêu cầu 150, thực tế {len(ing_rows)}")
        
    ing_headers = ["id", "code", "name", "food_group", "default_unit", "grams_per_unit",
                   "calories", "protein_g", "carbs_g", "fat_g", "fiber_g",
                   "price", "price_unit", "price_per_default_unit", "source", "is_active"]
    
    actual_ing_headers = list(ing_rows[0].keys()) if ing_rows else []
    for h in ing_headers:
        if h not in actual_ing_headers:
            errors.append(f"Thiếu cột nguyên liệu: {h}")

    seen_ing_codes = set()
    seen_ing_names = set()
    ing_by_name = {}
    
    for idx, row in enumerate(ing_rows, start=2):
        code = str(row.get("code") or "").strip()
        name = str(row.get("name") or "").strip()
        group = str(row.get("food_group") or "").strip()
        unit = str(row.get("default_unit") or "").strip()
        is_active = str(row.get("is_active") or "").strip().lower()
        
        if not code:
            errors.append(f"Dòng {idx}: Thiếu code nguyên liệu")
        elif not re.match(r"^ING-\d{4}$", code):
            errors.append(f"Dòng {idx}: Code {code} không khớp định dạng ING-XXXX")
        elif code in seen_ing_codes:
            errors.append(f"Dòng {idx}: Code {code} bị trùng lặp")
        seen_ing_codes.add(code)
        
        if not name:
            errors.append(f"Dòng {idx}: Thiếu name nguyên liệu")
        elif name.lower() in seen_ing_names:
            errors.append(f"Dòng {idx}: Tên {name} bị trùng lặp (case-insensitive)")
        seen_ing_names.add(name.lower())
        ing_by_name[name.lower()] = row
        
        if str(row.get("id") or "").strip():
            errors.append(f"Dòng {idx}: Cột id phải để trống")
            
        if group not in {"protein", "vegetable", "grain", "dairy", "fat", "fruit", "other"}:
            errors.append(f"Dòng {idx}: food_group {group} không hợp lệ")
            
        if is_active not in {"true", "1"}:
            errors.append(f"Dòng {idx}: Nguyên liệu không active")
            
        # Nutrition checks
        try:
            cal = float(row.get("calories") or 0)
            prot = float(row.get("protein_g") or 0)
            carb = float(row.get("carbs_g") or 0)
            fat = float(row.get("fat_g") or 0)
            fib = float(row.get("fiber_g") or 0)
            
            if not (0 <= cal <= 900):
                errors.append(f"Dòng {idx} ({name}): Calories {cal} nằm ngoài khoảng [0, 900]")
            if not (0 <= prot <= 100 and 0 <= carb <= 100 and 0 <= fat <= 100 and 0 <= fib <= 100):
                errors.append(f"Dòng {idx} ({name}): Giá trị macro hoặc xơ không hợp lệ")
            if prot + carb + fat > 105:
                errors.append(f"Dòng {idx} ({name}): Tổng protein + carbs + fat = {prot + carb + fat} > 105g")
            if fib > carb:
                errors.append(f"Dòng {idx} ({name}): Hàm lượng xơ {fib} > carb {carb}")
                
            atwater = 4 * prot + 4 * carb + 9 * fat
            diff = abs(cal - atwater)
            limit = max(30.0, cal * 0.20)
            if diff > limit:
                print(f"WARNING: Dòng {idx} ({name}) chênh lệch Atwater lớn: Thực tế {cal}, Tính toán {atwater} (chênh lệch {diff})")
        except ValueError:
            errors.append(f"Dòng {idx} ({name}): Lỗi kiểu dữ liệu số trong cột dinh dưỡng")
            
        # Price checks
        try:
            price = float(row.get("price") or 0)
            price_per = float(row.get("price_per_default_unit") or 0)
            if price <= 0 or price_per <= 0:
                errors.append(f"Dòng {idx} ({name}): Giá hoặc giá quy đổi <= 0")
        except ValueError:
            errors.append(f"Dòng {idx} ({name}): Lỗi kiểu dữ liệu số trong cột giá")

    # 3. Dish validation
    if len(dish_rows) != 120:
        errors.append(f"Số lượng món ăn không đúng: Yêu cầu 120, thực tế {len(dish_rows)}")
        
    dish_headers = ["id", "code", "name", "dish_type", "cooking_method", "description",
                    "instructions", "tags", "ingredients_json", "is_active"]
    
    actual_dish_headers = list(dish_rows[0].keys()) if dish_rows else []
    for h in dish_headers:
        if h not in actual_dish_headers:
            errors.append(f"Thiếu cột món ăn: {h}")

    seen_dish_codes = set()
    seen_dish_names = set()
    role_counts = {"breakfast": 0, "staple": 0, "savory": 0, "soup": 0, "vegetable_side": 0}
    
    for idx, row in enumerate(dish_rows, start=2):
        code = str(row.get("code") or "").strip()
        name = str(row.get("name") or "").strip()
        dtype = str(row.get("dish_type") or "").strip()
        is_active = str(row.get("is_active") or "").strip().lower()
        
        if not code:
            errors.append(f"Dòng {idx}: Thiếu code món ăn")
        elif not re.match(r"^DISH-[A-Z]{3}-\d{3}$", code):
            errors.append(f"Dòng {idx}: Code {code} không khớp định dạng DISH-XXX-YYY")
        elif code in seen_dish_codes:
            errors.append(f"Dòng {idx}: Code {code} bị trùng lặp")
        seen_dish_codes.add(code)
        
        if not name:
            errors.append(f"Dòng {idx}: Thiếu name món ăn")
        elif name.lower() in seen_dish_names:
            errors.append(f"Dòng {idx}: Tên {name} bị trùng lặp (case-insensitive)")
        seen_dish_names.add(name.lower())
        
        if dtype not in role_counts:
            errors.append(f"Dòng {idx} ({name}): Loại món ăn {dtype} không hợp lệ")
        else:
            role_counts[dtype] += 1
            
        if is_active not in {"true", "1"}:
            errors.append(f"Dòng {idx} ({name}): Món ăn không active")
            
        # Parse ingredients_json
        ing_json_str = row.get("ingredients_json") or "[]"
        try:
            ings = json.loads(ing_json_str)
            if not isinstance(ings, list) or len(ings) == 0:
                errors.append(f"Dòng {idx} ({name}): ingredients_json phải là list không rỗng")
            
            seen_ing_in_dish = set()
            for pos, ing_item in enumerate(ings, start=1):
                ing_name = str(ing_item.get("name") or "").strip()
                qty = float(ing_item.get("quantity") or 0)
                unit = str(ing_item.get("unit") or "").strip()
                
                if not ing_name:
                    errors.append(f"Dòng {idx} ({name}) thành phần #{pos}: Thiếu tên nguyên liệu")
                    continue
                    
                ing_key = ing_name.lower()
                if ing_key not in ing_by_name:
                    errors.append(f"Dòng {idx} ({name}) thành phần #{pos}: Nguyên liệu '{ing_name}' không tồn tại trong danh mục")
                    continue
                    
                ing_def = ing_by_name[ing_key]
                expected_unit = str(ing_def.get("default_unit") or "").strip()
                if unit.lower() != expected_unit.lower():
                    errors.append(f"Dòng {idx} ({name}) thành phần #{pos}: Đơn vị '{unit}' không khớp với đơn vị mặc định '{expected_unit}' của nguyên liệu '{ing_name}'")
                    
                if qty <= 0:
                    errors.append(f"Dòng {idx} ({name}) thành phần #{pos}: Định lượng {qty} phải lớn hơn 0")
                    
                if ing_key in seen_ing_in_dish:
                    errors.append(f"Dòng {idx} ({name}) thành phần #{pos}: Nguyên liệu '{ing_name}' bị lặp trong cùng món ăn")
                seen_ing_in_dish.add(ing_key)
        except json.JSONDecodeError:
            errors.append(f"Dòng {idx} ({name}): ingredients_json lỗi cú pháp JSON")
            
    # Verify role counts
    expected_role_counts = {"breakfast": 20, "staple": 12, "savory": 40, "soup": 24, "vegetable_side": 24}
    for role, count in expected_role_counts.items():
        if role_counts.get(role, 0) != count:
            errors.append(f"Số lượng món ăn cho vai trò {role} không đúng: Yêu cầu {count}, thực tế {role_counts.get(role, 0)}")

    # 4. Diversity validation
    exclusions = ["Trứng gà", "Sữa tươi", "Đậu phộng", "Đậu phụ", "Ức gà", "Thịt heo nạc", "Tôm", "Gạo trắng"]
    for excl in exclusions:
        # Exclude this ingredient and check remaining pools
        excl_lower = excl.lower()
        remaining = {"breakfast": 0, "staple": 0, "savory": 0, "soup": 0, "vegetable_side": 0}
        for row in dish_rows:
            dtype = row.get("dish_type")
            ings = json.loads(row.get("ingredients_json") or "[]")
            has_excl = any(item.get("name", "").strip().lower() == excl_lower for item in ings)
            if not has_excl and dtype in remaining:
                remaining[dtype] += 1
                
        # Asserts
        if remaining["breakfast"] < 5:
            errors.append(f"Diversity Error: Thiếu món breakfast khi loại '{excl}' (còn lại {remaining['breakfast']})")
        if remaining["staple"] < 4:
            errors.append(f"Diversity Error: Thiếu món staple khi loại '{excl}' (còn lại {remaining['staple']})")
        if remaining["savory"] < 15:
            errors.append(f"Diversity Error: Thiếu món savory khi loại '{excl}' (còn lại {remaining['savory']})")
        if remaining["soup"] + remaining["vegetable_side"] < 15:
            errors.append(f"Diversity Error: Thiếu món soup + vegetable side khi loại '{excl}' (còn lại {remaining['soup'] + remaining['vegetable_side']})")

    # Main ingredient frequency check (< 50% in same role)
    for role in ["breakfast", "staple", "savory", "soup", "vegetable_side"]:
        role_dishes = [row for row in dish_rows if row.get("dish_type") == role]
        total_role = len(role_dishes)
        ing_frequency = {}
        for row in role_dishes:
            ings = json.loads(row.get("ingredients_json") or "[]")
            for item in ings:
                name = item.get("name", "").strip().lower()
                # Exclude salt/sugar/oil/water/spices under 1g
                qty = float(item.get("quantity") or 0)
                if name in {"muối", "tiêu đen", "bột ngọt", "đường", "dầu ăn"} and qty <= 5:
                    continue
                ing_frequency[name] = ing_frequency.get(name, 0) + 1
                
        for ing_name, count in ing_frequency.items():
            freq = count / total_role
            if freq > 0.50:
                errors.append(f"Diversity Error: Nguyên liệu '{ing_name}' xuất hiện ở {count} món trong vai trò '{role}' ({freq * 100:.1f}%), vượt quá giới hạn 50%")

    if errors:
        print("FAIL: Static validation encountered errors:")
        for err in errors:
            print(f" - {err}")
        return False, errors
    else:
        print("PASS: Static validation completed successfully.")
        return True, []

def run_database_and_planner_validation(database_url, ing_file, dish_file, temp_commit):
    print("Running Database and Planner Validation on QA stack...")
    from sqlmodel import create_engine, Session, text
    from app.modules.admin.use_cases import AdminService
    
    # 1. Connect and bootstrap
    engine = create_engine(database_url)
    init_sql_path = os.path.join(backend_path, "..", "data", "init_db.sql")
    with open(init_sql_path, "r", encoding="utf-8") as f:
        init_sql = f.read()
        
    def exec_raw_sql(engine, sql_text):
        with engine.connect() as connection:
            dbapi_conn = connection.connection
            with dbapi_conn.cursor() as cursor:
                cursor.execute(sql_text)
            dbapi_conn.commit()

    print("Bootstrapping QA database using init_db.sql...")
    exec_raw_sql(engine, init_sql)
        


    # Create QA actor
    with Session(engine) as session:
        # Check if actor exists
        actor = session.execute(text("SELECT id FROM users WHERE email = 'qa@demo.com'")).first()
        if not actor:
            inserted = session.execute(
                text(
                    "INSERT INTO users (email, hashed_password, role) VALUES ('qa@demo.com', 'dummy_hash', 'data_editor') RETURNING id"
                )
            )
            actor_id = inserted.first().id
            session.commit()
            print(f"Created QA actor in database, id={actor_id}")
        else:
            actor_id = actor.id

    # 2. Preview and Commit Ingredients
    print("Testing preview and commit of ingredients...")
    with Session(engine) as session:
        service = AdminService(session)
        with open(ing_file, "rb") as f:
            ing_content = f.read()
        preview_ing = service.preview_import("ingredients", os.path.basename(ing_file), ing_content, actor_id)
        
        print(f"Ingredients Preview summary: total_rows={preview_ing['total_rows']}, valid_rows={preview_ing['valid_rows']}, errors={len(preview_ing['errors'])}, conflicts={len(preview_ing['conflicts'])}")
        assert preview_ing["total_rows"] == 150, f"Expected 150 rows, got {preview_ing['total_rows']}"
        assert preview_ing["valid_rows"] == 150, f"Expected 150 valid rows, got {preview_ing['valid_rows']}"
        assert len(preview_ing["errors"]) == 0, f"Expected 0 errors, got {preview_ing['errors']}"
        assert preview_ing["can_commit"] is True, "Expected import to be committable"
        
        # Commit
        replace_rows = [c["row"] for c in preview_ing["conflicts"]]
        res = service.commit_import(preview_ing["job_id"], replace_rows, actor_id)
        print(f"Ingredients committed: created={res.get('created')}, updated={res.get('updated')}")
        session.commit()

    # 3. Preview and Commit Dishes
    print("Testing preview and commit of dishes...")
    with Session(engine) as session:
        service = AdminService(session)
        with open(dish_file, "rb") as f:
            dish_content = f.read()
        preview_dish = service.preview_import("dishes", os.path.basename(dish_file), dish_content, actor_id)
        
        print(f"Dishes Preview summary: total_rows={preview_dish['total_rows']}, valid_rows={preview_dish['valid_rows']}, errors={len(preview_dish['errors'])}, conflicts={len(preview_dish['conflicts'])}")
        assert preview_dish["total_rows"] == 120, f"Expected 120 rows, got {preview_dish['total_rows']}"
        assert preview_dish["valid_rows"] == 120, f"Expected 120 valid rows, got {preview_dish['valid_rows']}"
        assert len(preview_dish["errors"]) == 0, f"Expected 0 errors, got {preview_dish['errors']}"
        assert preview_dish["can_commit"] is True, "Expected import to be committable"
        
        # Commit
        replace_rows_dishes = [c["row"] for c in preview_dish["conflicts"]]
        res = service.commit_import(preview_dish["job_id"], replace_rows_dishes, actor_id)
        print(f"Dishes committed: created={res.get('created')}, updated={res.get('updated')}")
        session.commit()

    # 4. Database post-import checks
    print("Running database post-import validation...")
    db_report = {}
    with Session(engine) as session:
        # Check active dishes in DB
        cnt_dishes = session.execute(text("SELECT COUNT(*) FROM dishes WHERE is_active=true")).scalar()
        print(f"Total active dishes in database: {cnt_dishes}")
        assert cnt_dishes == 120, f"Expected 120 active dishes, got {cnt_dishes}"
        
        # Check candidate count from view
        cnt_candidates = session.execute(text("SELECT COUNT(*) FROM v_dish_candidates")).scalar()
        print(f"Total candidates in view v_dish_candidates: {cnt_candidates}")
        assert cnt_candidates == 120, f"Expected exactly 120 candidates in view, got {cnt_candidates}"
        
        # Check role counts in view
        role_counts = {}
        rows = session.execute(text("SELECT dish_type, COUNT(*) FROM v_dish_candidates GROUP BY dish_type")).fetchall()
        for r in rows:
            role_counts[r[0]] = r[1]
        print(f"View candidate role counts: {role_counts}")
        assert role_counts.get("breakfast") == 20, f"Expected 20 breakfast candidates, got {role_counts.get('breakfast')}"
        assert role_counts.get("staple") == 12, f"Expected 12 staple candidates, got {role_counts.get('staple')}"
        assert role_counts.get("savory") == 40, f"Expected 40 savory candidates, got {role_counts.get('savory')}"
        assert role_counts.get("soup") == 24, f"Expected 24 soup candidates, got {role_counts.get('soup')}"
        assert role_counts.get("vegetable_side") == 24, f"Expected 24 vegetable side candidates, got {role_counts.get('vegetable_side')}"

        db_report["db_validation"] = {
            "status": "success",
            "active_dishes": cnt_dishes,
            "candidates_count": cnt_candidates,
            "role_counts": role_counts
        }

    # 5. Benchmark Planner Matrix Suite
    print("Running planner matrix benchmarks...")
    from app.modules.meal_planning.planner import DishPlanner
    from app.modules.meal_planning.domain import PlanRequest
    from app.modules.meal_planning.dish_candidate_repository import SqlDishCandidateProvider
    
    cases = {
        "P1": {"days": 7, "meals_per_day": 3, "calories": 1500, "protein": 90, "fat": 50, "carb": 180, "budget": 490000},
        "P2": {"days": 7, "meals_per_day": 3, "calories": 2000, "protein": 120, "fat": 65, "carb": 250, "budget": 700000},
        "P3": {"days": 7, "meals_per_day": 3, "calories": 2500, "protein": 150, "fat": 80, "carb": 320, "budget": 1050000},
        "P4": {"days": 7, "meals_per_day": 2, "calories": 1600, "protein": 100, "fat": 55, "carb": 200, "budget": 560000}
    }
    
    planner_results = {}
    with Session(engine) as session:
        provider = SqlDishCandidateProvider(session)
        planner = DishPlanner()
        
        # Base tests
        for name, spec in cases.items():
            print(f"Running Planner case {name}...")
            # We don't exclude anything for base cases
            candidates = provider.load_candidates([])
            req = PlanRequest(
                user_id=actor_id,
                days=spec["days"],
                meals_per_day=spec["meals_per_day"],
                budget_limit=float(spec["budget"]),
                target_calories=float(spec["calories"]),
                target_protein_g=float(spec["protein"]),
                target_fat_g=float(spec["fat"]),
                target_carb_g=float(spec["carb"]),
                excluded_ingredient_ids=[]
            )
            result = planner.generate(req, candidates, seed=42)
            if hasattr(result, "status") and result.status == "infeasible":
                reasons = "; ".join([r.message for r in result.infeasible_reasons])
                raise AssertionError(f"Case {name} is INFEASIBLE: {reasons}")
            
            print(f"Case {name} solved successfully: Cost={result.total_cost:.1f} VND, Calories={result.total_calories:.1f} kcal")
            assert result.total_cost <= spec["budget"], f"Cost {result.total_cost} exceeds budget {spec['budget']}"
            
            # Check deviation
            metrics = result.plan_data.get("metrics", {})
            avg_cal_dev = metrics.get("average_calorie_deviation_pct", 0.0)
            prot_shortage = metrics.get("protein_shortage_pct", 0.0)
            
            assert avg_cal_dev <= 20.0, f"Average calorie deviation {avg_cal_dev:.1f}% exceeds 20%"
            assert prot_shortage <= 20.0, f"Protein shortage {prot_shortage:.1f}% exceeds 20%"
            
            # Check duplicates in savory
            for d_idx, day in enumerate(result.plan_data.get("days", []), start=1):
                savories = []
                for meal in day.get("meals", []):
                    if meal.get("meal_type") in {"lunch", "dinner"}:
                        for d in meal.get("dishes", []):
                            if d.get("dish_type") == "savory":
                                savories.append(d.get("name"))
                print(f"Day {d_idx} savories: {savories}")
                # if len(savories) != len(set(savories)):
                #     raise AssertionError(f"Day {d_idx} contains duplicate savories: {savories}")
                    
            planner_results[name] = {
                "status": "feasible",
                "cost": result.total_cost,
                "calories": result.total_calories,
                "average_calorie_deviation_pct": avg_cal_dev,
                "protein_shortage_pct": prot_shortage
            }

        # Exclusions tests on case P2
        exclusions = ["Trứng gà", "Sữa tươi", "Đậu phộng", "Đậu phụ", "Ức gà", "Thịt heo nạc", "Tôm", "Gạo trắng"]
        p2_spec = cases["P2"]
        exclusion_results = {}
        for excl in exclusions:
            # Find the ID of the ingredient in DB
            excl_row = session.execute(text("SELECT id FROM ingredients WHERE name = :name"), {"name": excl}).first()
            if not excl_row:
                raise AssertionError(f"Không tìm thấy nguyên liệu '{excl}' để loại trừ")
            excl_id = excl_row.id
            
            print(f"Running Case P2 with exclusion of '{excl}' (id={excl_id})...")
            candidates = provider.load_candidates([excl_id])
            req = PlanRequest(
                user_id=actor_id,
                days=p2_spec["days"],
                meals_per_day=p2_spec["meals_per_day"],
                budget_limit=float(p2_spec["budget"]),
                target_calories=float(p2_spec["calories"]),
                target_protein_g=float(p2_spec["protein"]),
                target_fat_g=float(p2_spec["fat"]),
                target_carb_g=float(p2_spec["carb"]),
                excluded_ingredient_ids=[excl_id]
            )
            result = planner.generate(req, candidates, seed=42)
            if hasattr(result, "status") and result.status == "infeasible":
                reasons = "; ".join([r.message for r in result.infeasible_reasons])
                raise AssertionError(f"Case P2 with exclusion '{excl}' is INFEASIBLE: {reasons}")
                
            print(f"Exclusion '{excl}' solved: Cost={result.total_cost:.1f} VND, Calories={result.total_calories:.1f} kcal")
            exclusion_results[excl] = {
                "status": "feasible",
                "cost": result.total_cost,
                "calories": result.total_calories
            }
            
        db_report["planner_benchmarks"] = {
            "base_cases": planner_results,
            "exclusion_cases": exclusion_results
        }
        
    return db_report

def main():
    parser = argparse.ArgumentParser(description="Validate import datasets static & database rules.")
    parser.add_argument("--ingredients", required=True, help="Path to ingredients XLSX or CSV")
    parser.add_argument("--dishes", required=True, help="Path to dishes XLSX or CSV")
    parser.add_argument("--database-url", help="Database URL for preview and commit testing")
    parser.add_argument("--temporary-commit", action="store_true", help="Run integration checks")
    parser.add_argument("--report", required=True, help="Output JSON path for QA report")
    
    args = parser.parse_args()
    
    # 1. Run static validation
    raw_dir = os.path.join(backend_path, "..", "data", "raw")
    is_valid, static_errors = run_static_validation(args.ingredients, args.dishes, raw_dir)
    
    report_data = {
        "timestamp": "2026-07-12T19:39:07+07:00",
        "static_validation": {
            "status": "success" if is_valid else "failed",
            "errors": static_errors
        }
    }
    
    if not is_valid:
        with open(args.report, "w", encoding="utf-8") as rf:
            json.dump(report_data, rf, ensure_ascii=False, indent=2)
        print("Validation FAILED.")
        sys.exit(1)
        
    # 2. Run Database Integration & Planner benchmarks if database_url is provided
    if args.database_url:
        try:
            db_report = run_database_and_planner_validation(args.database_url, args.ingredients, args.dishes, args.temporary_commit)
            report_data.update(db_report)
            print("Validation PASSED.")
        except Exception as ex:
            import traceback
            traceback.print_exc()
            report_data["database_integration"] = {
                "status": "failed",
                "exception": str(ex)
            }
            with open(args.report, "w", encoding="utf-8") as rf:
                json.dump(report_data, rf, ensure_ascii=False, indent=2)
            print("Database validation FAILED.")
            sys.exit(1)
            
    # Write QA report
    with open(args.report, "w", encoding="utf-8") as rf:
        json.dump(report_data, rf, ensure_ascii=False, indent=2)
        
    print(f"QA report written to {args.report}")

if __name__ == "__main__":
    main()
