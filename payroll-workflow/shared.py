TASK_QUEUE_NAME = "payroll"

# The query and signal scripts attach to the running workflow by its ID.
# Using a fixed ID here means you can run those scripts without copying an
# ID between terminal windows. A real system would derive this from the
# employee's identifier, so that each employee has their own payroll workflow.
WORKFLOW_ID = "payroll-employee-1001"
