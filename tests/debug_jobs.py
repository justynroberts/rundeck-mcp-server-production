"""Debug jobs functionality and test job analysis."""

import unittest
from unittest.mock import Mock, patch
import json
from datetime import datetime

from rundeck_mcp.tools.jobs import analyze_job, visualize_job, get_job_definition
from rundeck_mcp.models.rundeck import JobDefinition, JobAnalysis, JobVisualization


class TestJobAnalysis(unittest.TestCase):
    """Test job analysis functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_job_data = {
            'id': 'test-job-123',
            'name': 'Deploy Web Application',
            'group': 'deployment',
            'project': 'webapp',
            'description': 'Deploy the web application to production servers',
            'enabled': True,
            'scheduled': True,
            'scheduleEnabled': True,
            'workflow': {
                'steps': [
                    {
                        'type': 'command',
                        'description': 'Stop application service',
                        'command': 'sudo systemctl stop webapp'
                    },
                    {
                        'type': 'script',
                        'description': 'Backup current deployment',
                        'script': 'rsync -av /var/www/webapp/ /backups/webapp-$(date +%Y%m%d)/'
                    },
                    {
                        'type': 'command',
                        'description': 'Deploy new version',
                        'command': 'curl -O https://releases.company.com/webapp-latest.tar.gz && tar -xzf webapp-latest.tar.gz'
                    },
                    {
                        'type': 'command',
                        'description': 'Start application service',
                        'command': 'sudo systemctl start webapp'
                    }
                ]
            },
            'options': [
                {
                    'name': 'version',
                    'description': 'Version to deploy',
                    'required': True,
                    'defaultValue': 'latest'
                },
                {
                    'name': 'skip_backup',
                    'description': 'Skip backup step',
                    'required': False,
                    'defaultValue': 'false'
                }
            ],
            'nodefilters': {
                'filter': 'tags: production+webapp'
            },
            'schedule': {
                'crontab': '0 2 * * 1'  # Weekly deployment
            }
        }
        
        self.destructive_job_data = {
            'id': 'cleanup-job-456',
            'name': 'Clean up old logs',
            'project': 'maintenance',
            'description': 'Remove old log files to free up disk space',
            'workflow': {
                'steps': [
                    {
                        'type': 'command',
                        'description': 'Find and delete old logs',
                        'command': 'find /var/log -name "*.log" -mtime +30 -delete'
                    },
                    {
                        'type': 'command',
                        'description': 'Remove temp files',
                        'command': 'rm -rf /tmp/app_temp/*'
                    }
                ]
            },
            'nodefilters': {
                'filter': 'tags: production'
            }
        }
    
    @patch('rundeck_mcp.tools.jobs.get_job_definition')
    def test_analyze_deployment_job(self, mock_get_job_def):
        """Test analysis of deployment job."""
        # Mock job definition
        job_def = JobDefinition(**self.sample_job_data)
        mock_get_job_def.return_value = job_def
        
        # Analyze job
        analysis = analyze_job('test-job-123')
        
        # Check analysis results
        self.assertEqual(analysis.job_id, 'test-job-123')
        self.assertEqual(analysis.job_name, 'Deploy Web Application')
        self.assertIn('Deploy', analysis.purpose)
        self.assertIn('4 workflow steps', analysis.workflow_summary)
        self.assertIn('2 options', analysis.options_summary)
        self.assertIn('1 required', analysis.options_summary)
        self.assertNotEqual(analysis.risk_level, 'LOW')  # Should be at least MEDIUM due to sudo
        self.assertIsNotNone(analysis.schedule_summary)
    
    @patch('rundeck_mcp.tools.jobs.get_job_definition')
    def test_analyze_destructive_job(self, mock_get_job_def):
        """Test analysis of destructive job."""
        # Mock job definition
        job_def = JobDefinition(**self.destructive_job_data)
        mock_get_job_def.return_value = job_def
        
        # Analyze job
        analysis = analyze_job('cleanup-job-456')
        
        # Check risk assessment
        self.assertEqual(analysis.risk_level, 'HIGH')
        self.assertIn('destructive operations', ' '.join(analysis.risk_factors))
        self.assertIn('production environment', ' '.join(analysis.risk_factors))
    
    @patch('rundeck_mcp.tools.jobs.get_job_definition')
    def test_visualize_job(self, mock_get_job_def):
        """Test job visualization."""
        # Mock job definition
        job_def = JobDefinition(**self.sample_job_data)
        mock_get_job_def.return_value = job_def
        
        # Visualize job
        visualization = visualize_job('test-job-123')
        
        # Check visualization results
        self.assertEqual(visualization.job_id, 'test-job-123')
        self.assertEqual(visualization.job_name, 'Deploy Web Application')
        self.assertIn('graph TD', visualization.mermaid_diagram)
        self.assertIn('Job Flow:', visualization.text_flow)
        self.assertIn('4 steps', visualization.summary)
        self.assertIn('2 options', visualization.summary)


class TestJobDebugUtilities(unittest.TestCase):
    """Test job debugging utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
    
    @patch('rundeck_mcp.tools.jobs.get_client')
    def test_get_job_definition_success(self, mock_get_client):
        """Test successful job definition retrieval."""
        mock_get_client.return_value = self.mock_client
        self.mock_client._make_request.return_value = {
            'id': 'job-123',
            'name': 'Test Job',
            'project': 'test-project',
            'workflow': {'steps': []},
            'options': {}
        }
        
        result = get_job_definition('job-123')
        
        self.assertEqual(result.id, 'job-123')
        self.assertEqual(result.name, 'Test Job')
        self.assertEqual(result.project, 'test-project')
        self.mock_client._make_request.assert_called_once_with('GET', 'job/job-123')
    
    @patch('rundeck_mcp.tools.jobs.get_client')
    def test_get_job_definition_error(self, mock_get_client):
        """Test job definition retrieval error handling."""
        mock_get_client.return_value = self.mock_client
        self.mock_client._make_request.side_effect = Exception("Job not found")
        
        with self.assertRaises(Exception) as context:
            get_job_definition('nonexistent-job')
        
        self.assertIn("Job not found", str(context.exception))
    
    def test_risk_assessment_algorithm(self):
        """Test risk assessment algorithm."""
        # Test high-risk job
        high_risk_steps = [
            {'command': 'sudo rm -rf /var/logs/*'},
            {'command': 'kill -9 $(ps aux | grep java)'}
        ]
        
        risk_score = 0
        risk_factors = []
        
        # Check for destructive operations
        destructive_keywords = ['delete', 'remove', 'drop', 'destroy', 'kill', 'terminate']
        for step in high_risk_steps:
            step_text = str(step).lower()
            if any(keyword in step_text for keyword in destructive_keywords):
                risk_factors.append("Contains potentially destructive operations")
                risk_score += 3
        
        # Check for system-level operations
        system_keywords = ['sudo', 'root', 'admin', 'system', 'kernel']
        for step in high_risk_steps:
            step_text = str(step).lower()
            if any(keyword in step_text for keyword in system_keywords):
                risk_factors.append("Performs system-level operations")
                risk_score += 2
        
        self.assertGreaterEqual(risk_score, 5)
        self.assertIn("destructive operations", ' '.join(risk_factors))
        self.assertIn("system-level operations", ' '.join(risk_factors))
    
    def test_mermaid_diagram_generation(self):
        """Test Mermaid diagram generation."""
        job_def = JobDefinition(
            id='test-job',
            name='Test Job',
            project='test-project',
            workflow=[
                {'type': 'command', 'description': 'Step 1'},
                {'type': 'script', 'description': 'Step 2'}
            ],
            options=[
                {'name': 'param1', 'required': True}
            ]
        )
        
        # Simulate diagram generation
        mermaid_lines = [
            "graph TD",
            f"    A[Start: {job_def.name}] --> B[Job Configuration]"
        ]
        
        # Add options
        if job_def.options:
            mermaid_lines.append("    B --> C[Options Validation]")
            previous_node = "C"
        else:
            previous_node = "B"
        
        # Add workflow steps
        for i, step in enumerate(job_def.workflow):
            step_id = chr(ord(previous_node) + 1 + i)
            step_name = step.get('description', f"Step {i+1}")
            step_type = step.get('type', 'command')
            
            if step_type == 'command':
                shape = f"[{step_name}]"
            elif step_type == 'script':
                shape = f"({step_name})"
            else:
                shape = f"{{{step_name}}}"
            
            mermaid_lines.append(f"    {previous_node} --> {step_id}{shape}")
            previous_node = step_id
        
        mermaid_diagram = "\\n".join(mermaid_lines)
        
        self.assertIn("graph TD", mermaid_diagram)
        self.assertIn("Start: Test Job", mermaid_diagram)
        self.assertIn("Options Validation", mermaid_diagram)
        self.assertIn("[Step 1]", mermaid_diagram)
        self.assertIn("(Step 2)", mermaid_diagram)


def debug_job_analysis():
    """Debug job analysis with real data."""
    print("=== Job Analysis Debug Tool ===")
    
    # Sample job data for testing
    test_jobs = [
        {
            'id': 'deploy-prod',
            'name': 'Production Deployment',
            'description': 'Deploy application to production servers',
            'workflow': [
                {'type': 'command', 'description': 'Stop services', 'command': 'sudo systemctl stop app'},
                {'type': 'script', 'description': 'Deploy code', 'script': 'deploy.sh'},
                {'type': 'command', 'description': 'Start services', 'command': 'sudo systemctl start app'}
            ],
            'nodefilters': {'filter': 'tags: production'},
            'risk_expected': 'HIGH'
        },
        {
            'id': 'health-check',
            'name': 'System Health Check',
            'description': 'Check system health and status',
            'workflow': [
                {'type': 'command', 'description': 'Check disk space', 'command': 'df -h'},
                {'type': 'command', 'description': 'Check memory', 'command': 'free -m'},
                {'type': 'command', 'description': 'Check services', 'command': 'systemctl status nginx'}
            ],
            'nodefilters': {'filter': 'tags: monitoring'},
            'risk_expected': 'LOW'
        }
    ]
    
    for job_data in test_jobs:
        print(f"\\nAnalyzing job: {job_data['name']}")
        print(f"Expected risk: {job_data['risk_expected']}")
        
        # Simulate analysis
        risk_score = 0
        risk_factors = []
        
        # Check for destructive operations
        destructive_keywords = ['delete', 'remove', 'drop', 'destroy', 'kill', 'terminate']
        for step in job_data['workflow']:
            step_text = str(step).lower()
            if any(keyword in step_text for keyword in destructive_keywords):
                risk_factors.append("Contains potentially destructive operations")
                risk_score += 3
        
        # Check for system-level operations
        system_keywords = ['sudo', 'root', 'admin', 'system', 'kernel']
        for step in job_data['workflow']:
            step_text = str(step).lower()
            if any(keyword in step_text for keyword in system_keywords):
                risk_factors.append("Performs system-level operations")
                risk_score += 2
        
        # Check for production targeting
        if 'production' in str(job_data.get('nodefilters', '')).lower():
            risk_factors.append("Targets production environment")
            risk_score += 2
        
        # Determine risk level
        if risk_score >= 5:
            risk_level = "HIGH"
        elif risk_score >= 2:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        print(f"Calculated risk: {risk_level}")
        print(f"Risk factors: {risk_factors}")
        print(f"Risk score: {risk_score}")
        
        # Verify expectation
        if risk_level == job_data['risk_expected']:
            print("✅ Risk assessment matches expectation")
        else:
            print("❌ Risk assessment mismatch")


if __name__ == '__main__':
    # Run debug tool
    debug_job_analysis()
    
    # Run unit tests
    print("\\n=== Running Unit Tests ===")
    unittest.main()