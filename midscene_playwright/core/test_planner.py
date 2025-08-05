"""
AI-powered test planner for intelligent test case generation and execution
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from .ai_engine import QwenVLEngine

logger = logging.getLogger(__name__)


class TestPlanner:
    """
    AI-powered test planner that generates intelligent test plans and execution strategies
    
    Features:
    - Automatic test step generation based on UI analysis
    - Risk assessment and failure prediction
    - Adaptive test planning based on page complexity
    - Data-driven test case optimization
    """
    
    def __init__(self, ai_engine: QwenVLEngine):
        """
        Initialize TestPlanner
        
        Args:
            ai_engine: AI engine for analysis and planning
        """
        self.ai_engine = ai_engine
        
        # Test planning templates and patterns
        self._common_patterns = self._load_common_patterns()
        self._risk_factors = self._load_risk_factors()
        
        # Planning history for adaptive improvement
        self._planning_history: List[Dict[str, Any]] = []
        self._max_history = 100
        
        logger.debug("Initialized TestPlanner")
    
    async def create_plan(
        self,
        screenshot: Union[bytes, str],
        objective: str,
        current_url: Optional[str] = None,
        context: Optional[str] = None,
        complexity_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a comprehensive test plan based on screenshot and objective
        
        Args:
            screenshot: Screenshot of current page state
            objective: Test objective description
            current_url: Current page URL
            context: Additional context about the test
            complexity_hint: Hint about expected complexity (low, medium, high)
            
        Returns:
            Detailed test plan dictionary
        """
        try:
            logger.info(f"Creating test plan for objective: {objective}")
            
            # Get AI-generated test plan
            ai_plan = self.ai_engine.plan_test_steps(
                screenshot=screenshot,
                test_objective=objective,
                current_url=current_url
            )
            
            # Enhance the plan with additional intelligence
            enhanced_plan = await self._enhance_test_plan(
                ai_plan, objective, context, complexity_hint
            )
            
            # Add risk assessment
            risk_analysis = self._assess_risks(enhanced_plan, objective)
            enhanced_plan.update(risk_analysis)
            
            # Add execution strategy
            execution_strategy = self._create_execution_strategy(enhanced_plan)
            enhanced_plan["execution_strategy"] = execution_strategy
            
            # Record planning for adaptive improvement
            self._record_planning(objective, enhanced_plan)
            
            logger.info(f"Created test plan with {len(enhanced_plan.get('steps', []))} steps")
            return enhanced_plan
            
        except Exception as e:
            logger.error(f"Error creating test plan: {str(e)}")
            return self._create_fallback_plan(objective, str(e))
    
    async def _enhance_test_plan(
        self,
        ai_plan: Dict[str, Any],
        objective: str,
        context: Optional[str],
        complexity_hint: Optional[str]
    ) -> Dict[str, Any]:
        """
        Enhance AI-generated test plan with additional intelligence
        
        Args:
            ai_plan: Base plan from AI
            objective: Test objective
            context: Additional context
            complexity_hint: Complexity hint
            
        Returns:
            Enhanced test plan
        """
        enhanced_plan = ai_plan.copy()
        
        try:
            # Enhance test steps with additional metadata
            steps = enhanced_plan.get("steps", [])
            enhanced_steps = []
            
            for i, step in enumerate(steps):
                enhanced_step = step.copy()
                
                # Add step metadata
                enhanced_step.update({
                    "step_id": f"step_{i+1:03d}",
                    "estimated_duration": self._estimate_step_duration(step),
                    "retry_strategy": self._get_retry_strategy(step),
                    "validation_criteria": self._generate_validation_criteria(step),
                    "error_recovery": self._get_error_recovery_actions(step),
                    "screenshot_checkpoints": self._should_take_screenshot(step)
                })
                
                enhanced_steps.append(enhanced_step)
            
            enhanced_plan["steps"] = enhanced_steps
            
            # Add plan metadata
            test_plan_info = enhanced_plan.get("test_plan", {})
            test_plan_info.update({
                "plan_id": self._generate_plan_id(),
                "created_at": self._get_timestamp(),
                "adaptive_features": self._get_adaptive_features(objective),
                "parallel_execution": self._assess_parallel_capability(steps),
                "resource_requirements": self._assess_resource_requirements(steps)
            })
            
            enhanced_plan["test_plan"] = test_plan_info
            
            # Add monitoring and reporting
            enhanced_plan["monitoring"] = {
                "performance_tracking": True,
                "screenshot_intervals": self._calculate_screenshot_intervals(steps),
                "failure_detection": self._get_failure_detection_config(),
                "progress_reporting": True
            }
            
            return enhanced_plan
            
        except Exception as e:
            logger.warning(f"Error enhancing test plan: {str(e)}")
            return ai_plan
    
    def _assess_risks(self, plan: Dict[str, Any], objective: str) -> Dict[str, Any]:
        """
        Assess risks and potential failure points in the test plan
        
        Args:
            plan: Test plan to assess
            objective: Test objective
            
        Returns:
            Risk assessment results
        """
        try:
            steps = plan.get("steps", [])
            risk_analysis = {
                "overall_risk_level": "low",
                "risk_factors": [],
                "mitigation_strategies": [],
                "critical_points": [],
                "failure_probability": 0.1
            }
            
            risk_score = 0.0
            risk_factors = []
            critical_points = []
            
            for i, step in enumerate(steps):
                step_risks = self._analyze_step_risks(step, i)
                risk_score += step_risks["score"]
                risk_factors.extend(step_risks["factors"])
                
                if step_risks["is_critical"]:
                    critical_points.append({
                        "step_number": step.get("step_number", i+1),
                        "description": step.get("description", "Unknown step"),
                        "risk_reasons": step_risks["factors"]
                    })
            
            # Calculate overall risk level
            avg_risk = risk_score / max(len(steps), 1)
            if avg_risk > 0.7:
                risk_analysis["overall_risk_level"] = "high"
            elif avg_risk > 0.4:
                risk_analysis["overall_risk_level"] = "medium"
            
            risk_analysis["risk_factors"] = list(set(risk_factors))
            risk_analysis["critical_points"] = critical_points
            risk_analysis["failure_probability"] = min(avg_risk, 0.9)
            
            # Generate mitigation strategies
            risk_analysis["mitigation_strategies"] = self._generate_mitigation_strategies(
                risk_factors, critical_points
            )
            
            return {"risk_analysis": risk_analysis}
            
        except Exception as e:
            logger.warning(f"Error assessing risks: {str(e)}")
            return {"risk_analysis": {"overall_risk_level": "unknown", "error": str(e)}}
    
    def _analyze_step_risks(self, step: Dict[str, Any], step_index: int) -> Dict[str, Any]:
        """
        Analyze risks for a specific test step
        
        Args:
            step: Test step to analyze
            step_index: Index of the step
            
        Returns:
            Step risk analysis
        """
        action = step.get("action", "").lower()
        target = step.get("target", "").lower()
        
        risk_factors = []
        risk_score = 0.1  # Base risk
        
        # Action-based risks
        if action in ["click", "type"]:
            # Element interaction risks
            if "dynamic" in target or "ajax" in target:
                risk_factors.append("Dynamic content interaction")
                risk_score += 0.3
            
            if step_index == 0:
                risk_factors.append("First action - page may not be fully loaded")
                risk_score += 0.2
        
        elif action == "navigate":
            risk_factors.append("Network dependency")
            risk_score += 0.2
            
            if "external" in target or "http" in target:
                risk_factors.append("External URL dependency")
                risk_score += 0.3
        
        elif action == "wait":
            timeout_value = step.get("value", "30")
            if timeout_value.isdigit() and int(timeout_value) > 10:
                risk_factors.append("Long wait time")
                risk_score += 0.2
        
        elif action == "verify":
            risk_factors.append("Verification step - may be subjective")
            risk_score += 0.1
        
        # Target-based risks
        if any(term in target for term in ["popup", "modal", "dialog"]):
            risk_factors.append("Modal/popup interaction")
            risk_score += 0.3
        
        if any(term in target for term in ["dropdown", "select", "menu"]):
            risk_factors.append("Complex UI element")
            risk_score += 0.2
        
        if any(term in target for term in ["file", "upload", "download"]):
            risk_factors.append("File operation")
            risk_score += 0.4
        
        # Determine if step is critical
        is_critical = (
            risk_score > 0.6 or
            action in ["navigate", "verify"] or
            step_index == 0 or
            "login" in target or
            "submit" in target
        )
        
        return {
            "score": min(risk_score, 1.0),
            "factors": risk_factors,
            "is_critical": is_critical
        }
    
    def _create_execution_strategy(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create execution strategy based on plan analysis
        
        Args:
            plan: Test plan to create strategy for
            
        Returns:
            Execution strategy configuration
        """
        steps = plan.get("steps", [])
        risk_level = plan.get("risk_analysis", {}).get("overall_risk_level", "medium")
        
        strategy = {
            "execution_mode": "sequential",  # Default to sequential
            "retry_policy": self._get_retry_policy(risk_level),
            "timeout_strategy": self._get_timeout_strategy(steps),
            "failure_handling": self._get_failure_handling_strategy(risk_level),
            "parallel_groups": [],
            "checkpoints": self._define_checkpoints(steps),
            "recovery_points": self._define_recovery_points(steps)
        }
        
        # Determine if parallel execution is possible
        parallel_groups = self._identify_parallel_groups(steps)
        if parallel_groups:
            strategy["execution_mode"] = "hybrid"
            strategy["parallel_groups"] = parallel_groups
        
        return strategy
    
    def _get_retry_policy(self, risk_level: str) -> Dict[str, Any]:
        """Get retry policy based on risk level"""
        policies = {
            "low": {"max_retries": 2, "delay": 1.0, "backoff": 1.5},
            "medium": {"max_retries": 3, "delay": 2.0, "backoff": 2.0},
            "high": {"max_retries": 5, "delay": 3.0, "backoff": 2.5}
        }
        
        return policies.get(risk_level, policies["medium"])
    
    def _get_timeout_strategy(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get timeout strategy based on step analysis"""
        step_count = len(steps)
        has_navigation = any(step.get("action") == "navigate" for step in steps)
        has_complex_interactions = any(
            "dropdown" in step.get("target", "").lower() or
            "upload" in step.get("target", "").lower()
            for step in steps
        )
        
        base_timeout = 30000  # 30 seconds
        if has_navigation:
            base_timeout += 15000
        if has_complex_interactions:
            base_timeout += 10000
        if step_count > 10:
            base_timeout += 5000
        
        return {
            "default_timeout": base_timeout,
            "navigation_timeout": base_timeout + 15000,
            "interaction_timeout": base_timeout - 10000,
            "verification_timeout": 10000
        }
    
    def _identify_parallel_groups(self, steps: List[Dict[str, Any]]) -> List[List[int]]:
        """Identify steps that can be executed in parallel"""
        # This is a simplified implementation
        # In practice, you'd need more sophisticated dependency analysis
        
        parallel_groups = []
        verification_steps = []
        
        for i, step in enumerate(steps):
            if step.get("action") == "verify":
                verification_steps.append(i)
        
        # Group verification steps that don't depend on each other
        if len(verification_steps) > 1:
            parallel_groups.append(verification_steps)
        
        return parallel_groups
    
    def _define_checkpoints(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Define checkpoints for test execution monitoring"""
        checkpoints = []
        
        for i, step in enumerate(steps):
            action = step.get("action", "")
            
            # Add checkpoints at critical points
            if (action in ["navigate", "verify"] or 
                i == 0 or 
                i == len(steps) - 1 or
                "login" in step.get("target", "").lower()):
                
                checkpoints.append({
                    "step_number": step.get("step_number", i+1),
                    "checkpoint_type": "critical" if action == "verify" else "standard",
                    "description": f"Checkpoint after {action}",
                    "validation_required": action == "verify"
                })
        
        return checkpoints
    
    def _define_recovery_points(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Define recovery points for error handling"""
        recovery_points = []
        
        for i, step in enumerate(steps):
            if step.get("action") == "navigate" or "login" in step.get("target", "").lower():
                recovery_points.append({
                    "step_number": step.get("step_number", i+1),
                    "recovery_type": "restart_from_navigation" if step.get("action") == "navigate" else "re_authenticate",
                    "description": f"Recovery point at step {i+1}",
                    "prerequisites": []
                })
        
        return recovery_points
    
    def _estimate_step_duration(self, step: Dict[str, Any]) -> float:
        """Estimate duration for a test step in seconds"""
        action = step.get("action", "").lower()
        
        duration_map = {
            "navigate": 5.0,
            "click": 1.0,
            "type": 2.0,
            "wait": float(step.get("value", "3")) if step.get("value", "").isdigit() else 3.0,
            "scroll": 1.5,
            "verify": 2.0
        }
        
        base_duration = duration_map.get(action, 2.0)
        
        # Add complexity factors
        target = step.get("target", "").lower()
        if any(term in target for term in ["dropdown", "modal", "popup"]):
            base_duration *= 1.5
        if "upload" in target or "download" in target:
            base_duration *= 2.0
        
        return base_duration
    
    def _get_retry_strategy(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Get retry strategy for a specific step"""
        action = step.get("action", "").lower()
        
        if action == "navigate":
            return {"max_retries": 3, "delay": 2.0}
        elif action in ["click", "type"]:
            return {"max_retries": 2, "delay": 1.0}
        elif action == "verify":
            return {"max_retries": 1, "delay": 0.5}
        else:
            return {"max_retries": 2, "delay": 1.0}
    
    def _generate_validation_criteria(self, step: Dict[str, Any]) -> List[str]:
        """Generate validation criteria for a step"""
        action = step.get("action", "").lower()
        criteria = []
        
        if action == "navigate":
            criteria.extend([
                "Page loaded successfully",
                "URL matches expected pattern",
                "No network errors"
            ])
        elif action == "click":
            criteria.extend([
                "Element was clickable",
                "Click action completed",
                "Page state changed as expected"
            ])
        elif action == "type":
            criteria.extend([
                "Input field was accessible",
                "Text was entered successfully",
                "Input validation passed"
            ])
        elif action == "verify":
            criteria.extend([
                "Verification criteria met",
                "Expected elements present",
                "Page state matches requirements"
            ])
        
        return criteria
    
    def _get_error_recovery_actions(self, step: Dict[str, Any]) -> List[str]:
        """Get error recovery actions for a step"""
        action = step.get("action", "").lower()
        
        recovery_map = {
            "navigate": ["Refresh page", "Check network connection", "Retry with different URL"],
            "click": ["Wait for element", "Scroll to element", "Try alternative selector"],
            "type": ["Clear field first", "Check field is enabled", "Try alternative input method"],
            "verify": ["Take screenshot", "Check page source", "Wait longer for changes"],
            "wait": ["Reduce timeout", "Check element exists", "Skip if optional"]
        }
        
        return recovery_map.get(action, ["Retry action", "Take screenshot", "Continue if possible"])
    
    def _should_take_screenshot(self, step: Dict[str, Any]) -> bool:
        """Determine if screenshot should be taken for this step"""
        action = step.get("action", "").lower()
        target = step.get("target", "").lower()
        
        # Always screenshot for important actions
        if action in ["navigate", "verify"]:
            return True
        
        # Screenshot for login-related actions
        if "login" in target or "password" in target:
            return True
        
        # Screenshot for form submissions
        if "submit" in target or action == "submit":
            return True
        
        return False
    
    def _load_common_patterns(self) -> Dict[str, Any]:
        """Load common test patterns and templates"""
        return {
            "login_flow": {
                "steps": ["navigate", "type_username", "type_password", "click_login", "verify_success"],
                "validations": ["check_login_form", "verify_credentials", "confirm_redirect"]
            },
            "form_submission": {
                "steps": ["fill_required_fields", "validate_inputs", "submit_form", "verify_submission"],
                "validations": ["check_required_fields", "validate_format", "confirm_success"]
            },
            "navigation_flow": {
                "steps": ["click_menu", "select_option", "verify_navigation"],
                "validations": ["check_menu_available", "verify_page_change"]
            }
        }
    
    def _load_risk_factors(self) -> Dict[str, float]:
        """Load known risk factors and their weights"""
        return {
            "network_dependency": 0.3,
            "dynamic_content": 0.4,
            "external_service": 0.5,
            "file_operation": 0.6,
            "popup_interaction": 0.3,
            "form_validation": 0.2,
            "authentication": 0.4,
            "javascript_heavy": 0.3
        }
    
    def _generate_plan_id(self) -> str:
        """Generate unique plan ID"""
        import uuid
        return f"plan_{uuid.uuid4().hex[:8]}"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _get_adaptive_features(self, objective: str) -> List[str]:
        """Get adaptive features based on objective"""
        features = ["smart_retry", "dynamic_timeout"]
        
        if "login" in objective.lower():
            features.append("authentication_optimization")
        if "form" in objective.lower():
            features.append("form_validation_enhancement")
        if "search" in objective.lower():
            features.append("search_result_validation")
        
        return features
    
    def _assess_parallel_capability(self, steps: List[Dict[str, Any]]) -> bool:
        """Assess if steps can be executed in parallel"""
        # Simple heuristic: if there are multiple verification steps
        verification_count = sum(1 for step in steps if step.get("action") == "verify")
        return verification_count > 1
    
    def _assess_resource_requirements(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess resource requirements for the test plan"""
        return {
            "memory": "standard",
            "network": "required" if any(step.get("action") == "navigate" for step in steps) else "optional",
            "storage": "minimal",
            "browser_features": self._get_required_browser_features(steps)
        }
    
    def _get_required_browser_features(self, steps: List[Dict[str, Any]]) -> List[str]:
        """Get required browser features"""
        features = ["javascript"]
        
        for step in steps:
            target = step.get("target", "").lower()
            if "file" in target or "upload" in target:
                features.append("file_system_access")
            if "camera" in target or "microphone" in target:
                features.append("media_permissions")
            if "location" in target or "geolocation" in target:
                features.append("geolocation")
        
        return list(set(features))
    
    def _calculate_screenshot_intervals(self, steps: List[Dict[str, Any]]) -> List[int]:
        """Calculate when to take screenshots during execution"""
        intervals = []
        
        for i, step in enumerate(steps):
            if self._should_take_screenshot(step):
                intervals.append(i)
        
        return intervals
    
    def _get_failure_detection_config(self) -> Dict[str, Any]:
        """Get failure detection configuration"""
        return {
            "timeout_detection": True,
            "element_not_found_detection": True,
            "network_error_detection": True,
            "javascript_error_detection": True,
            "unexpected_navigation_detection": True
        }
    
    def _generate_mitigation_strategies(
        self,
        risk_factors: List[str],
        critical_points: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate mitigation strategies for identified risks"""
        strategies = []
        
        for factor in risk_factors:
            if "dynamic content" in factor.lower():
                strategies.append("Implement smart waiting strategies for dynamic content")
            if "network" in factor.lower():
                strategies.append("Add network connectivity checks and retries")
            if "popup" in factor.lower() or "modal" in factor.lower():
                strategies.append("Implement popup/modal detection and handling")
            if "file" in factor.lower():
                strategies.append("Add file operation validation and error handling")
        
        if critical_points:
            strategies.append("Implement checkpoint-based recovery for critical steps")
            strategies.append("Add enhanced logging for critical operations")
        
        return list(set(strategies))
    
    def _get_failure_handling_strategy(self, risk_level: str) -> Dict[str, Any]:
        """Get failure handling strategy based on risk level"""
        strategies = {
            "low": {
                "continue_on_failure": True,
                "max_consecutive_failures": 2,
                "recovery_mode": "simple"
            },
            "medium": {
                "continue_on_failure": False,
                "max_consecutive_failures": 1,
                "recovery_mode": "checkpoint"
            },
            "high": {
                "continue_on_failure": False,
                "max_consecutive_failures": 1,
                "recovery_mode": "full_recovery"
            }
        }
        
        return strategies.get(risk_level, strategies["medium"])
    
    def _record_planning(self, objective: str, plan: Dict[str, Any]):
        """Record planning session for adaptive improvement"""
        try:
            record = {
                "timestamp": self._get_timestamp(),
                "objective": objective,
                "plan_complexity": len(plan.get("steps", [])),
                "risk_level": plan.get("risk_analysis", {}).get("overall_risk_level"),
                "features_used": plan.get("test_plan", {}).get("adaptive_features", [])
            }
            
            self._planning_history.append(record)
            
            # Maintain history size
            if len(self._planning_history) > self._max_history:
                self._planning_history.pop(0)
                
        except Exception as e:
            logger.warning(f"Error recording planning session: {str(e)}")
    
    def _create_fallback_plan(self, objective: str, error: str) -> Dict[str, Any]:
        """Create a simple fallback plan when AI planning fails"""
        return {
            "test_plan": {
                "objective": objective,
                "estimated_steps": 1,
                "complexity": "error",
                "estimated_time": "unknown",
                "plan_id": self._generate_plan_id(),
                "created_at": self._get_timestamp()
            },
            "steps": [{
                "step_number": 1,
                "action": "manual_review",
                "target": "page",
                "description": f"Manual review required due to planning error: {error}",
                "expected_result": "Manual verification completed",
                "verification": "Human verification required",
                "step_id": "step_001"
            }],
            "prerequisites": [],
            "success_criteria": ["Manual review completed successfully"],
            "potential_failures": [f"Planning failed: {error}"],
            "data_requirements": [],
            "risk_analysis": {
                "overall_risk_level": "unknown",
                "risk_factors": ["AI planning failure"],
                "mitigation_strategies": ["Manual test execution"],
                "critical_points": [],
                "failure_probability": 1.0
            },
            "execution_strategy": {
                "execution_mode": "manual",
                "retry_policy": {"max_retries": 0, "delay": 0},
                "failure_handling": {"continue_on_failure": False}
            }
        }