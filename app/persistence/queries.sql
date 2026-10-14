-- TECH5 Representative Relational SQL Queries
-- Demonstrates filtering, joins, grouping, aggregation, subqueries, and historical retrieval

-- 1. Full Solution Assignments View (Multi-table Join & Filtering)
-- Retrieves comprehensive allocation details with student names and project titles.
SELECT
    a.solution_id,
    s.id AS student_id,
    s.display_name AS student_name,
    p.id AS project_id,
    p.title AS project_title,
    a.is_fixed,
    a.preference_rank,
    a.skill_fit_score,
    a.unmet_requirements
FROM assignments a
JOIN students s ON a.student_id = s.id
JOIN projects p ON a.project_id = p.id
WHERE a.solution_id = :solution_id
ORDER BY a.preference_rank IS NULL, a.preference_rank ASC, s.display_name ASC;


-- 2. Project Capacity Utilization & Demand Aggregate
-- Compares allocated headcount against maximum and minimum capacities.
SELECT
    p.id AS project_id,
    p.title AS project_title,
    p.min_capacity,
    p.max_capacity,
    COUNT(a.id) AS assigned_count,
    ROUND(COUNT(a.id) * 100.0 / p.max_capacity, 1) AS utilization_percentage,
    (p.max_capacity - COUNT(a.id)) AS remaining_seats,
    CASE
        WHEN COUNT(a.id) > p.max_capacity THEN 'OVER_CAPACITY'
        WHEN COUNT(a.id) < p.min_capacity THEN 'UNDER_MINIMUM'
        WHEN COUNT(a.id) = p.max_capacity THEN 'FULL'
        ELSE 'AVAILABLE'
    END AS capacity_status
FROM projects p
LEFT JOIN assignments a ON p.id = a.project_id AND a.solution_id = :solution_id
GROUP BY p.id, p.title, p.min_capacity, p.max_capacity
ORDER BY utilization_percentage DESC;


-- 3. Preference Satisfaction Distribution (Aggregation & Filtering)
-- Measures fairness and distribution of assigned preference ranks.
SELECT
    COALESCE(CAST(a.preference_rank AS TEXT), 'Unranked / Outside Preference') AS rank_bucket,
    COUNT(a.id) AS student_count,
    ROUND(COUNT(a.id) * 100.0 / (SELECT COUNT(*) FROM assignments WHERE solution_id = :solution_id), 1) AS percentage_of_cohort
FROM assignments a
WHERE a.solution_id = :solution_id
GROUP BY a.preference_rank
ORDER BY a.preference_rank IS NULL, a.preference_rank ASC;


-- 4. Unmet Skill Requirements & Competence Gap Analysis (Subquery & Outer Joins)
-- Identifies student-project allocations where project skill requirements are unmet.
SELECT
    a.solution_id,
    s.id AS student_id,
    s.display_name AS student_name,
    p.id AS project_id,
    p.title AS project_title,
    pr.skill_id,
    sk.name AS skill_name,
    pr.minimum_level AS required_level,
    COALESCE(ss.level, 0) AS student_level,
    (pr.minimum_level - COALESCE(ss.level, 0)) AS skill_deficit,
    pr.is_mandatory
FROM assignments a
JOIN students s ON a.student_id = s.id
JOIN projects p ON a.project_id = p.id
JOIN project_requirements pr ON p.id = pr.project_id
JOIN skills sk ON pr.skill_id = sk.id
LEFT JOIN student_skills ss ON s.id = ss.student_id AND pr.skill_id = ss.skill_id
WHERE a.solution_id = :solution_id
  AND COALESCE(ss.level, 0) < pr.minimum_level
ORDER BY pr.is_mandatory DESC, skill_deficit DESC;


-- 5. Fixed Assignment Integrity Audit (Anti-join / Validation Query)
-- Verifies that every fixed assignment is strictly honored in the generated solution.
SELECT
    fa.student_id,
    fa.project_id AS required_project_id,
    fa.reason,
    a.project_id AS actual_project_id,
    CASE
        WHEN a.project_id = fa.project_id THEN 'HONORED'
        WHEN a.project_id IS NULL THEN 'UNASSIGNED'
        ELSE 'VIOLATED'
    END AS compliance_status
FROM fixed_assignments fa
LEFT JOIN assignments a ON fa.student_id = a.student_id AND a.solution_id = :solution_id;


-- 6. Historical Runs Overview with Solution Counts and Timestamps
SELECT
    r.id AS run_id,
    r.created_at,
    r.status,
    COUNT(s.id) AS alternative_solutions_count,
    r.configuration
FROM assignment_runs r
LEFT JOIN solutions s ON r.id = s.run_id
GROUP BY r.id, r.created_at, r.status, r.configuration
ORDER BY r.created_at DESC
LIMIT 25;
