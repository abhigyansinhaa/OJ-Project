"""
Code execution service for the Online Judge.

This module handles the secure execution of user-submitted code against test cases.
It supports Python, C++, C, and Java languages.
"""

import subprocess
import tempfile
import os
import logging
from pathlib import Path
from typing import Tuple, Optional
from dataclasses import dataclass
from django.utils import timezone

from submit.models import Submission, SubmissionTestResult, SubmissionStatus
from problems.models import TestCase

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of executing code against a single test case."""
    status: str
    actual_output: str = ""
    error_message: str = ""
    runtime_ms: int = 0
    memory_kb: int = 0


class CodeExecutor:
    """
    Executes user code against test cases in a secure environment.
    
    Supports: Python, C++, C, Java
    """
    
    # Language configurations
    LANGUAGE_CONFIG = {
        'py': {
            'extension': '.py',
            'compile_cmd': None,  # Python is interpreted
            'run_cmd': ['python'],
        },
        'cpp': {
            'extension': '.cpp',
            'compile_cmd': ['g++', '-o', '{executable}', '{source}', '-std=c++17'],
            'run_cmd': ['{executable}'],
        },
        'c': {
            'extension': '.c',
            'compile_cmd': ['gcc', '-o', '{executable}', '{source}'],
            'run_cmd': ['{executable}'],
        },
        'java': {
            'extension': '.java',
            'compile_cmd': ['javac', '{source}'],
            'run_cmd': ['java', '-cp', '{workdir}', 'Solution'],
            'filename': 'Solution.java',  # Java requires specific filename
        },
    }

    def __init__(self, submission: Submission):
        self.submission = submission
        self.problem = submission.problem
        self.language = submission.language
        self.code = submission.code
        self.config = self.LANGUAGE_CONFIG.get(self.language)
        
        if not self.config:
            raise ValueError(f"Unsupported language: {self.language}")

    def execute_all(self) -> None:
        """Execute the submission against all test cases and update the database."""
        logger.info(f"Starting execution for submission {self.submission.id}")
        
        # Update status to running
        self.submission.status = SubmissionStatus.RUNNING
        self.submission.save()
        
        # Get all test cases for this problem
        test_cases = TestCase.objects.filter(problem=self.problem).order_by('order')
        total_tests = test_cases.count()
        passed_tests = 0
        final_status = SubmissionStatus.ACCEPTED
        total_runtime = 0
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write code to file
                source_path, executable_path = self._prepare_files(temp_dir)
                
                # Compile if needed
                compile_result = self._compile(source_path, executable_path, temp_dir)
                if compile_result:
                    # Compilation error
                    self.submission.status = SubmissionStatus.COMPILATION_ERROR
                    self.submission.error_message = compile_result
                    self.submission.tests_total = total_tests
                    self.submission.tests_passed = 0
                    self.submission.judged_at = timezone.now()
                    self.submission.save()
                    logger.warning(f"Compilation error for submission {self.submission.id}")
                    return
                
                # Run against each test case
                for test_case in test_cases:
                    result = self._run_test(
                        source_path, executable_path, temp_dir, test_case
                    )
                    
                    # Save test result
                    SubmissionTestResult.objects.create(
                        submission=self.submission,
                        test_case=test_case,
                        status=result.status,
                        actual_output=result.actual_output,
                        runtime_ms=result.runtime_ms,
                        memory_kb=result.memory_kb,
                        error_message=result.error_message
                    )
                    
                    total_runtime += result.runtime_ms
                    
                    if result.status == SubmissionStatus.ACCEPTED:
                        passed_tests += 1
                    else:
                        # First failing test determines the final status
                        if final_status == SubmissionStatus.ACCEPTED:
                            final_status = result.status
                
                # Update submission with final results
                self.submission.status = final_status
                self.submission.tests_passed = passed_tests
                self.submission.tests_total = total_tests
                self.submission.runtime_ms = total_runtime
                self.submission.judged_at = timezone.now()
                self.submission.save()
                
                # Update problem statistics
                self._update_problem_stats(final_status == SubmissionStatus.ACCEPTED)
                
                logger.info(
                    f"Submission {self.submission.id} completed: "
                    f"{passed_tests}/{total_tests} tests passed, status={final_status}"
                )
                
        except Exception as e:
            logger.exception(f"Error executing submission {self.submission.id}")
            self.submission.status = SubmissionStatus.RUNTIME_ERROR
            self.submission.error_message = str(e)
            self.submission.judged_at = timezone.now()
            self.submission.save()

    def _prepare_files(self, temp_dir: str) -> Tuple[Path, Path]:
        """Write code to file and return paths."""
        filename = self.config.get('filename', f'solution{self.config["extension"]}')
        source_path = Path(temp_dir) / filename
        executable_path = Path(temp_dir) / 'solution'
        
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(self.code)
        
        return source_path, executable_path

    def _compile(self, source_path: Path, executable_path: Path, temp_dir: str) -> Optional[str]:
        """
        Compile the code if needed.
        Returns error message if compilation fails, None otherwise.
        """
        compile_cmd = self.config.get('compile_cmd')
        if not compile_cmd:
            return None  # Interpreted language
        
        # Build the compile command
        cmd = [
            part.format(
                source=str(source_path),
                executable=str(executable_path),
                workdir=temp_dir
            )
            for part in compile_cmd
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second compile timeout
                cwd=temp_dir
            )
            
            if result.returncode != 0:
                return result.stderr or result.stdout or "Compilation failed"
            
            return None
            
        except subprocess.TimeoutExpired:
            return "Compilation timed out"
        except Exception as e:
            return f"Compilation error: {str(e)}"

    def _run_test(
        self,
        source_path: Path,
        executable_path: Path,
        temp_dir: str,
        test_case: TestCase
    ) -> ExecutionResult:
        """Run the code against a single test case."""
        
        # Build the run command
        run_cmd = self.config['run_cmd']
        cmd = [
            part.format(
                source=str(source_path),
                executable=str(executable_path),
                workdir=temp_dir
            )
            for part in run_cmd
        ]
        
        # For Python, add the source file to the command
        if self.language == 'py':
            cmd.append(str(source_path))
        
        time_limit = self.problem.time_limit
        
        try:
            import time
            start_time = time.time()
            
            result = subprocess.run(
                cmd,
                input=test_case.input_data,
                capture_output=True,
                text=True,
                timeout=time_limit + 0.5,  # Small buffer
                cwd=temp_dir
            )
            
            end_time = time.time()
            runtime_ms = int((end_time - start_time) * 1000)
            
            # Check for runtime error
            if result.returncode != 0:
                return ExecutionResult(
                    status=SubmissionStatus.RUNTIME_ERROR,
                    actual_output=result.stdout,
                    error_message=result.stderr,
                    runtime_ms=runtime_ms
                )
            
            # Compare output
            actual_output = result.stdout.strip()
            expected_output = test_case.expected_output.strip()
            
            if actual_output == expected_output:
                return ExecutionResult(
                    status=SubmissionStatus.ACCEPTED,
                    actual_output=actual_output,
                    runtime_ms=runtime_ms
                )
            else:
                return ExecutionResult(
                    status=SubmissionStatus.WRONG_ANSWER,
                    actual_output=actual_output,
                    runtime_ms=runtime_ms
                )
                
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                status=SubmissionStatus.TIME_LIMIT_EXCEEDED,
                runtime_ms=int(time_limit * 1000)
            )
        except Exception as e:
            return ExecutionResult(
                status=SubmissionStatus.RUNTIME_ERROR,
                error_message=str(e)
            )

    def _update_problem_stats(self, is_accepted: bool) -> None:
        """Update problem solve/attempt counts."""
        from django.db.models import F
        
        self.problem.attempt_count = F('attempt_count') + 1
        if is_accepted:
            # Check if this is the user's first accepted submission for this problem
            existing_accepted = Submission.objects.filter(
                user=self.submission.user,
                problem=self.problem,
                status=SubmissionStatus.ACCEPTED
            ).exclude(id=self.submission.id).exists()
            
            if not existing_accepted:
                self.problem.solve_count = F('solve_count') + 1
        
        self.problem.save(update_fields=['attempt_count', 'solve_count'])


def execute_submission(submission_id: int) -> None:
    """
    Execute a submission. This function can be called directly or via a task queue.
    """
    try:
        submission = Submission.objects.select_related('problem').get(id=submission_id)
        executor = CodeExecutor(submission)
        executor.execute_all()
    except Submission.DoesNotExist:
        logger.error(f"Submission {submission_id} not found")
    except Exception as e:
        logger.exception(f"Error executing submission {submission_id}: {e}")



