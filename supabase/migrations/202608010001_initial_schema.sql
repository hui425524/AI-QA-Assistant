create extension if not exists pgcrypto;

create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null,
  name varchar(120) not null check (char_length(name) between 1 and 120),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.requirement_versions (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  version integer not null check (version > 0),
  requirement_text text not null check (char_length(requirement_text) between 5 and 30000),
  requirement_score smallint not null check (requirement_score between 0 and 100),
  readiness_state varchar(16) not null check (readiness_state in ('blocked', 'ready')),
  missing_items jsonb not null default '[]'::jsonb check (jsonb_typeof(missing_items) = 'array'),
  clarification_questions jsonb not null default '[]'::jsonb check (jsonb_typeof(clarification_questions) = 'array'),
  analysis_json jsonb not null check (jsonb_typeof(analysis_json) = 'object'),
  provider varchar(40) not null,
  created_at timestamptz not null default now(),
  constraint uq_requirement_project_version unique (project_id, version)
);

create table if not exists public.test_cases (
  id uuid primary key default gen_random_uuid(),
  requirement_version_id uuid not null references public.requirement_versions(id) on delete cascade,
  case_id varchar(30) not null,
  scenario varchar(240) not null,
  preconditions text not null,
  steps jsonb not null check (jsonb_typeof(steps) = 'array'),
  test_data text not null,
  expected_result text not null,
  priority varchar(12) not null check (priority in ('High', 'Medium', 'Low')),
  test_type varchar(40) not null,
  created_at timestamptz not null default now(),
  constraint uq_test_case_version_case_id unique (requirement_version_id, case_id)
);

create index if not exists ix_projects_workspace_updated
  on public.projects (workspace_id, updated_at desc);
create index if not exists ix_requirement_versions_project_version
  on public.requirement_versions (project_id, version desc);
create index if not exists ix_test_cases_requirement_version
  on public.test_cases (requirement_version_id);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists projects_set_updated_at on public.projects;
create trigger projects_set_updated_at
before update on public.projects
for each row execute function public.set_updated_at();

create or replace function public.enforce_ready_requirement_version()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  current_state text;
begin
  select readiness_state
    into current_state
    from public.requirement_versions
   where id = new.requirement_version_id;

  if current_state is distinct from 'ready' then
    raise exception 'test cases require a ready requirement version'
      using errcode = '23514';
  end if;
  return new;
end;
$$;

drop trigger if exists test_cases_require_ready_version on public.test_cases;
create trigger test_cases_require_ready_version
before insert or update of requirement_version_id on public.test_cases
for each row execute function public.enforce_ready_requirement_version();

alter table public.projects enable row level security;
alter table public.requirement_versions enable row level security;
alter table public.test_cases enable row level security;

revoke all on table public.projects from anon, authenticated;
revoke all on table public.requirement_versions from anon, authenticated;
revoke all on table public.test_cases from anon, authenticated;

comment on table public.projects is
  'Server-owned anonymous workspaces. Supabase Auth replaces workspace_id in Phase 3.';
comment on table public.requirement_versions is
  'Immutable requirement analyses. Generation always reads the latest version.';
comment on table public.test_cases is
  'Cases traceable to one ready requirement version; protected by a database trigger.';
