-- TECH5 Relational Database Schema
-- Normalized 3NF Schema for Student-to-Project Assignment System

PRAGMA foreign_keys = ON;

-- Skills Catalog
CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT ''
);

-- Students Roster
CREATE TABLE IF NOT EXISTS students (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL
);

-- Projects Catalog
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    min_capacity INTEGER NOT NULL DEFAULT 0 CHECK(min_capacity >= 0),
    max_capacity INTEGER NOT NULL CHECK(max_capacity >= 1),
    CHECK(min_capacity <= max_capacity)
);

-- Student Skills Matrix (Many-to-Many with proficiency level)
CREATE TABLE IF NOT EXISTS student_skills (
    student_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    level INTEGER NOT NULL DEFAULT 1 CHECK(level >= 1),
    PRIMARY KEY (student_id, skill_id),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- Project Requirements Matrix (Many-to-Many with minimum required level)
CREATE TABLE IF NOT EXISTS project_requirements (
    project_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    minimum_level INTEGER NOT NULL DEFAULT 1 CHECK(minimum_level >= 1),
    is_mandatory INTEGER NOT NULL DEFAULT 0 CHECK(is_mandatory IN (0, 1)),
    PRIMARY KEY (project_id, skill_id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- Student Ranked Preferences
CREATE TABLE IF NOT EXISTS preferences (
    student_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    rank INTEGER NOT NULL CHECK(rank >= 1),
    PRIMARY KEY (student_id, project_id),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT uq_student_rank UNIQUE (student_id, rank)
);

-- Administrative Fixed Assignments (Locked pre-allocations)
CREATE TABLE IF NOT EXISTS fixed_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL UNIQUE,
    project_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'APPROVED',
    reason TEXT DEFAULT '',
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Historical Assignment Runs
CREATE TABLE IF NOT EXISTS assignment_runs (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL,
    configuration TEXT NOT NULL,
    diagnostics TEXT NOT NULL
);

-- Alternative Feasible Solutions Generated per Run
CREATE TABLE IF NOT EXISTS solutions (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    alternative_number INTEGER NOT NULL,
    strategy_name TEXT NOT NULL,
    objective_value REAL,
    indicators TEXT NOT NULL,
    warnings TEXT NOT NULL,
    diagnostics TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES assignment_runs(id) ON DELETE CASCADE,
    CONSTRAINT uq_run_alternative UNIQUE (run_id, alternative_number)
);

-- Detailed Student Allocations per Solution
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solution_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    is_fixed INTEGER NOT NULL DEFAULT 0 CHECK(is_fixed IN (0, 1)),
    preference_rank INTEGER,
    skill_fit_score REAL NOT NULL DEFAULT 0.0,
    unmet_requirements TEXT DEFAULT '[]',
    FOREIGN KEY (solution_id) REFERENCES solutions(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT uq_solution_student UNIQUE (solution_id, student_id)
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_student_skills_skill ON student_skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_project_requirements_skill ON project_requirements(skill_id);
CREATE INDEX IF NOT EXISTS idx_preferences_project ON preferences(project_id);
CREATE INDEX IF NOT EXISTS idx_solutions_run ON solutions(run_id);
CREATE INDEX IF NOT EXISTS idx_assignments_solution ON assignments(solution_id);
CREATE INDEX IF NOT EXISTS idx_assignments_project ON assignments(project_id);
CREATE INDEX IF NOT EXISTS idx_runs_created_at ON assignment_runs(created_at DESC);
