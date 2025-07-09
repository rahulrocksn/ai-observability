"""
Evaluation Dataset for Cognosys BI Agent
Tests the AI agent's ability to generate correct SQL queries and provide accurate answers
for business intelligence questions on the Northwind database.
"""

EVALUATION_QUESTIONS = [
    {
        "question": "Which country has the most customers?",
        "expected_sql_keywords": [
            "customers",
            "COUNT",
            "GROUP BY",
            "country",
            "ORDER BY",
            "LIMIT 1"
        ],
        "expected_answer_keywords": [
            "USA"
        ],
        "category": "customer_analysis",
        "difficulty": "easy"
    },
    
    {
        "question": "What is the name of the employee who has the most sales orders?",
        "expected_sql_keywords": [
            "employees",
            "orders",
            "COUNT",
            "JOIN",
            "GROUP BY",
            "employee_id"
        ],
        "expected_answer_keywords": [
            "Peacock"
        ],
        "category": "employee_performance",
        "difficulty": "medium",
        "note": "Based on the Northwind dataset, Margaret Peacock has the most orders."
    },
    
    {
        "question": "What are the top 3 best-selling products by total sales amount?",
        "expected_sql_keywords": [
            "order_details",
            "products",
            "SUM",
            "unit_price",
            "quantity",
            "LIMIT 3"
        ],
        "expected_answer_keywords": [
            "Côte de Blaye",
            "Thüringer",
            "Raclette"
        ],
        "category": "product_performance",
        "difficulty": "medium"
    },
    
    {
        "question": "How many customers are from Germany?",
        "expected_sql_keywords": [
            "customers",
            "COUNT",
            "WHERE",
            "country",
            "Germany"
        ],
        "expected_answer_keywords": [
            "11"
        ],
        "category": "customer_analysis",
        "difficulty": "easy"
    },
    
    {
        "question": "What is the average order value?",
        "expected_sql_keywords": [
            "order_details",
            "AVG",
            "unit_price",
            "quantity"
        ],
        "expected_answer_keywords": [
            "average"
        ],
        "category": "sales_analysis",
        "difficulty": "medium"
    },
    
    {
        "question": "Which supplier provides the most products?",
        "expected_sql_keywords": [
            "suppliers",
            "products",
            "COUNT",
            "JOIN",
            "GROUP BY",
            "supplier_id"
        ],
        "expected_answer_keywords": [
            "supplier"
        ],
        "category": "supply_chain",
        "difficulty": "medium"
    },
    
    {
        "question": "What are the top 5 customers by total order value?",
        "expected_sql_keywords": [
            "customers",
            "orders",
            "order_details",
            "SUM",
            "unit_price",
            "quantity",
            "JOIN",
            "GROUP BY",
            "customer_id",
            "LIMIT 5"
        ],
        "expected_answer_keywords": [
            "customer"
        ],
        "category": "customer_analysis",
        "difficulty": "hard"
    },
    
    {
        "question": "How many orders were placed in 1997?",
        "expected_sql_keywords": [
            "orders",
            "COUNT",
            "WHERE",
            "order_date",
            "1997"
        ],
        "expected_answer_keywords": [
            "1997"
        ],
        "category": "sales_analysis",
        "difficulty": "easy"
    },
    
    {
        "question": "Which product category has the highest average unit price?",
        "expected_sql_keywords": [
            "products",
            "categories",
            "AVG",
            "unit_price",
            "JOIN",
            "GROUP BY",
            "category_id"
        ],
        "expected_answer_keywords": [
            "category"
        ],
        "category": "product_analysis",
        "difficulty": "medium"
    },
    
    {
        "question": "What is the total revenue for each quarter of 1997?",
        "expected_sql_keywords": [
            "orders",
            "order_details",
            "SUM",
            "unit_price",
            "quantity",
            "EXTRACT",
            "QUARTER",
            "order_date",
            "WHERE",
            "1997"
        ],
        "expected_answer_keywords": [
            "quarter",
            "1997"
        ],
        "category": "financial_analysis",
        "difficulty": "hard"
    }
]

# Categories for organizing evaluation questions
CATEGORIES = {
    "customer_analysis": "Questions about customer data, segmentation, and behavior",
    "employee_performance": "Questions about employee sales and performance metrics",
    "product_performance": "Questions about product sales, rankings, and performance",
    "sales_analysis": "Questions about sales data, trends, and metrics",
    "supply_chain": "Questions about suppliers and supply chain relationships",
    "product_analysis": "Questions about product categories, pricing, and characteristics",
    "financial_analysis": "Questions about revenue, costs, and financial metrics"
}

# Difficulty levels
DIFFICULTY_LEVELS = {
    "easy": "Basic queries with simple WHERE clauses and aggregations",
    "medium": "Queries involving JOINs and more complex aggregations",
    "hard": "Complex queries with multiple JOINs, subqueries, or advanced functions"
}

def get_questions_by_category(category=None):
    """Get evaluation questions filtered by category."""
    if category:
        return [q for q in EVALUATION_QUESTIONS if q["category"] == category]
    return EVALUATION_QUESTIONS

def get_questions_by_difficulty(difficulty=None):
    """Get evaluation questions filtered by difficulty level."""
    if difficulty:
        return [q for q in EVALUATION_QUESTIONS if q["difficulty"] == difficulty]
    return EVALUATION_QUESTIONS

def get_random_question():
    """Get a random evaluation question."""
    import random
    return random.choice(EVALUATION_QUESTIONS)

def validate_sql_keywords(sql_query, expected_keywords):
    """Validate that SQL query contains expected keywords."""
    sql_upper = sql_query.upper()
    found_keywords = []
    missing_keywords = []
    
    for keyword in expected_keywords:
        if keyword.upper() in sql_upper:
            found_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)
    
    return {
        "found": found_keywords,
        "missing": missing_keywords,
        "score": len(found_keywords) / len(expected_keywords) if expected_keywords else 0
    }

def validate_answer_keywords(answer, expected_keywords):
    """Validate that answer contains expected keywords."""
    answer_lower = answer.lower()
    found_keywords = []
    missing_keywords = []
    
    for keyword in expected_keywords:
        if keyword.lower() in answer_lower:
            found_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)
    
    return {
        "found": found_keywords,
        "missing": missing_keywords,
        "score": len(found_keywords) / len(expected_keywords) if expected_keywords else 0
    }

def run_evaluation(agent, num_questions=None):
    """Run a comprehensive evaluation of the AI agent."""
    import random
    
    if num_questions:
        questions = random.sample(EVALUATION_QUESTIONS, min(num_questions, len(EVALUATION_QUESTIONS)))
    else:
        questions = EVALUATION_QUESTIONS
    
    results = []
    
    for question_data in questions:
        try:
            # Get agent response
            response = agent.invoke({"input": question_data["question"]})
            
            # Extract SQL and answer from response
            # This might need adjustment based on your agent's response format
            sql_query = response.get("sql", "")  # Adjust based on actual response format
            answer = response.get("output", "")
            
            # Validate SQL keywords
            sql_validation = validate_sql_keywords(sql_query, question_data["expected_sql_keywords"])
            
            # Validate answer keywords
            answer_validation = validate_answer_keywords(answer, question_data["expected_answer_keywords"])
            
            results.append({
                "question": question_data["question"],
                "category": question_data["category"],
                "difficulty": question_data["difficulty"],
                "sql_query": sql_query,
                "answer": answer,
                "sql_score": sql_validation["score"],
                "answer_score": answer_validation["score"],
                "sql_found": sql_validation["found"],
                "sql_missing": sql_validation["missing"],
                "answer_found": answer_validation["found"],
                "answer_missing": answer_validation["missing"]
            })
            
        except Exception as e:
            results.append({
                "question": question_data["question"],
                "error": str(e),
                "sql_score": 0,
                "answer_score": 0
            })
    
    return results

def print_evaluation_summary(results):
    """Print a summary of evaluation results."""
    if not results:
        print("No evaluation results to display.")
        return
    
    total_questions = len(results)
    successful_questions = len([r for r in results if "error" not in r])
    avg_sql_score = sum(r.get("sql_score", 0) for r in results) / total_questions
    avg_answer_score = sum(r.get("answer_score", 0) for r in results) / total_questions
    
    print(f"=== EVALUATION SUMMARY ===")
    print(f"Total Questions: {total_questions}")
    print(f"Successful Responses: {successful_questions}")
    print(f"Success Rate: {successful_questions/total_questions*100:.1f}%")
    print(f"Average SQL Score: {avg_sql_score:.2f}")
    print(f"Average Answer Score: {avg_answer_score:.2f}")
    
    # Category breakdown
    categories = {}
    for r in results:
        if "error" not in r:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = {"count": 0, "sql_score": 0, "answer_score": 0}
            categories[cat]["count"] += 1
            categories[cat]["sql_score"] += r["sql_score"]
            categories[cat]["answer_score"] += r["answer_score"]
    
    print(f"\n=== CATEGORY BREAKDOWN ===")
    for cat, stats in categories.items():
        avg_sql = stats["sql_score"] / stats["count"]
        avg_ans = stats["answer_score"] / stats["count"]
        print(f"{cat}: {stats['count']} questions, SQL: {avg_sql:.2f}, Answer: {avg_ans:.2f}")

if __name__ == "__main__":
    # Example usage
    print(f"Loaded {len(EVALUATION_QUESTIONS)} evaluation questions")
    print(f"Categories: {list(CATEGORIES.keys())}")
    print(f"Difficulty levels: {list(DIFFICULTY_LEVELS.keys())}")
    
    # Show a sample question
    sample = EVALUATION_QUESTIONS[0]
    print(f"\nSample question: {sample['question']}")
    print(f"Expected SQL keywords: {sample['expected_sql_keywords']}")
    print(f"Expected answer keywords: {sample['expected_answer_keywords']}") 