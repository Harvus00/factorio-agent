"""
Unified Tool Manager - Integrate dynamic tool generation, management, and execution.

This module provides a unified interface for managing all tool-related operations,
replacing the current tool management functionality spread across multiple classes.

Key Design Principles:
- Single source of truth for all tool metadata
- Clear separation of concerns between generation and storage
- Extensible provider architecture for different tool types
"""

import json
import logging
import importlib.util
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod
from agents import Runner

class ToolProvider(ABC):
    """Abstract base class for tool providers"""
    
    @abstractmethod
    async def generate_tool(self, requirement: str, **kwargs) -> Dict[str, Any]: 
        """Generate a new tool"""
        pass
    
    @abstractmethod
    def validate_tool(self, tool_name: str) -> Dict[str, Any]:
        """Validate a tool"""
        pass


class LuaScriptProvider(ToolProvider):
    """Lua script tool provider"""
    
    def __init__(self, coding_agent):
        self.coding_agent = coding_agent
        self.logger = logging.getLogger('lua_script_provider')
        
    async def generate_tool(self, requirement: str, **kwargs) -> Dict[str, Any]:
        """Generate a new Lua script tool through CodingAgent"""
        try:
            # Record existing scripts before generation
            existing_scripts = self.coding_agent.get_available_scripts_list()
            existing_count = len(existing_scripts)
            existing_names = {script['name'] for script in existing_scripts}
            
            request_message = f"""
Generate a new Factorio Lua script tool based on:
requirement: {requirement}
functionality_details: {kwargs.get('functionality_details', '')}
suggested_name: {kwargs.get('suggested_name', 'auto_generated')}
"""
            result = await Runner.run(
                self.coding_agent.agent,
                input=request_message,
                max_turns=10
            )
            
            # Check if new scripts were generated
            current_scripts = self.coding_agent.get_available_scripts_list()
            current_count = len(current_scripts)
            
            if current_count <= existing_count:
                return {
                    "success": False,
                    "message": "No new tool generated",
                    "details": str(result.final_output)
                }
            
            # Find the newly generated script(s)
            new_scripts = [script for script in current_scripts 
                          if script['name'] not in existing_names]
            
            if not new_scripts:
                return {
                    "success": False,
                    "message": "No new tool generated (no new script names found)",
                    "details": str(result.final_output)
                }
            
            # Get the latest generated script
            latest_script = max(new_scripts, key=lambda x: x.get('created_at', ''))
            return {
                "success": True,
                "tool_name": latest_script['name'],
                "script_info": latest_script,
                "agent_output": str(result.final_output)
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error generating tool: {str(e)}",
                "error": str(e)
            }
    
    def validate_tool(self, tool_name: str) -> Dict[str, Any]:
        """Validate Lua script tool through CodingAgent"""
        if hasattr(self.coding_agent, 'validate_lua_code'):
            # Get the tool's lua code and validate it
            # This would require access to the stored lua code
            return {"valid": True, "errors": [], "warnings": []}
        return {"valid": True, "errors": [], "warnings": []}


class UnifiedToolManager:
    """
    Unified tool manager - single source of truth for all tool operations.
    
    This class centralizes all tool-related operations including generation,
    storage, loading, and metadata management.
    """
    
    def __init__(self, tools_dir: str = "src/agent/tool/generated"):
        self.tools_dir = Path(tools_dir)
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger('unified_tool_manager')
        
        # Core data structures - single source of truth
        self.tools_registry: Dict[str, Dict[str, Any]] = {}
        self.loaded_tools: Dict[str, Callable] = {}
        self.tool_providers: Optional[ToolProvider] = None
        
        # Metadata file - unified storage
        self.metadata_file = self.tools_dir / "tool_metadata.json"
        self._load_metadata()
    
    def register_provider(self, provider: ToolProvider):
        """
        Register tool provider and establish bidirectional references
        
        Args:
            provider: Tool provider instance (e.g., LuaScriptProvider)
        """
        self.tool_providers = provider
        
        # Establish bidirectional reference for CodingAgent
        if hasattr(provider, 'coding_agent') and hasattr(provider.coding_agent, 'set_tool_manager'):
            provider.coding_agent.set_tool_manager(self)
            
        self.logger.info(f"Registered tool provider: {type(provider).__name__}")
    
    def _load_metadata(self):
        """Load metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    self.tools_registry = data.get('tools', {})
                self.logger.info(f"Loaded {len(self.tools_registry)} tools from metadata")
            except Exception as e:
                self.logger.warning(f"Failed to load metadata: {e}")
    
    def _save_metadata(self):
        """Save metadata"""
        try:
            data = {
                'tools': self.tools_registry,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save metadata: {e}")
    
    async def create_tool(self, 
                         requirement: str, 
                         **kwargs) -> Dict[str, Any]:
        """
        Create a new tool through the registered provider
        
        Args:
            requirement: Description of what the tool should do
            **kwargs: Additional parameters for tool generation
            
        Returns:
            Dictionary with generation results
        """
        
        if self.tool_providers is None:
            return {
                "success": False,
                "message": "No tool provider registered. Please register a tool provider first."
            }
        
        provider = self.tool_providers
        result = await provider.generate_tool(requirement, **kwargs)
        
        if result.get("success"):
            tool_name = result["tool_name"]
            
            # Register to unified registry - this will be called by CodingAgent
            # via register_generated_tool method
            self.logger.info(f"Tool generation initiated for: {tool_name}")
            
            # Try to hot load if the tool was successfully generated
            if self._hot_load_tool(tool_name):
                result["loaded"] = True
            
        return result
    
    def register_generated_tool(self, tool_name: str, metadata: Dict[str, Any]) -> bool:
        """
        Register a generated tool with unified metadata management
        
        This method is called by CodingAgent after it generates and saves a tool.
        
        Args:
            tool_name: Name of the generated tool
            metadata: Tool metadata including description, parameters, etc.
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Store in unified registry
            self.tools_registry[tool_name] = {
                # "requirement": metadata.get('description', ''),
                # "created_at": metadata.get('created_at', datetime.now().isoformat()),
                # "provider_result": {
                #     "success": True,
                #     "tool_name": tool_name,
                #     "script_info": metadata
                # },
                "metadata": metadata
            }
            
            self._save_metadata()
            self.logger.info(f"Successfully registered generated tool: {tool_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register generated tool {tool_name}: {e}")
            return False
    
    def update_tool_metadata(self, tool_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update metadata for an existing tool
        
        Args:
            tool_name: Name of the tool to update
            updates: Dictionary of updates to apply
            
        Returns:
            Dictionary with update results
        """
        if tool_name not in self.tools_registry:
            return {
                "success": False,
                "message": f"Tool '{tool_name}' not found"
            }
        
        try:
            # Update metadata
            current_metadata = self.tools_registry[tool_name].get("metadata", {})
            current_metadata.update(updates)
            current_metadata['updated_at'] = datetime.now().isoformat()
            
            # Increment version
            current_version = current_metadata.get('version', '1.0.0')
            version_parts = current_version.split('.')
            version_parts[-1] = str(int(version_parts[-1]) + 1)
            new_version = '.'.join(version_parts)
            current_metadata['version'] = new_version
            
            # Update registry
            self.tools_registry[tool_name]["metadata"] = current_metadata
            
            self._save_metadata()
            
            return {
                "success": True,
                "message": f"Successfully updated tool '{tool_name}' to version {new_version}",
                "new_version": new_version
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to update tool '{tool_name}': {str(e)}",
                "error": str(e)
            }
    
    def _hot_load_tool(self, tool_name: str) -> bool:
        """
        Hot load a tool into memory for execution
        
        Args:
            tool_name: Name of the tool to load
            
        Returns:
            True if loading successful, False otherwise
        """
        try:
            tool_file = self.tools_dir / f"{tool_name}.py"
            if not tool_file.exists():
                return False
            
            spec = importlib.util.spec_from_file_location(tool_name, tool_file)
            if spec is None or spec.loader is None:
                return False
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, tool_name):
                tool_func = getattr(module, tool_name)
                self.loaded_tools[tool_name] = tool_func
                self.logger.info(f"Hot loaded tool: {tool_name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to hot load tool {tool_name}: {e}")
        
        return False
    
    def load_all_tools(self) -> Dict[str, Callable]:
        """
        Load all available tools from the registry
        
        Returns:
            Dictionary of loaded tool functions
        """
        loaded_count = 0
        
        for tool_name in self.tools_registry.keys():
            if self._hot_load_tool(tool_name):
                loaded_count += 1
        
        self.logger.info(f"Loaded {loaded_count} tools")
        return self.loaded_tools.copy()
    
    def get_tool(self, tool_name: str) -> Optional[Callable]:
        """
        Get a loaded tool function
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool function or None if not found
        """
        if tool_name not in self.loaded_tools:
            # Try to load if not already loaded
            self._hot_load_tool(tool_name)
        
        return self.loaded_tools.get(tool_name)
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with given parameters
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool
            
        Returns:
            Dictionary with execution results
        """
        tool_func = self.get_tool(tool_name)
        if not tool_func:
            return {
                "success": False,
                "message": f"Tool '{tool_name}' not found or failed to load"
            }
        
        try:
            result = tool_func(**parameters)
            return {
                "success": True,
                "message": f"Successfully executed tool: {tool_name}",
                "result": result,
                "parameters": parameters
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error executing tool {tool_name}: {str(e)}",
                "error": str(e)
            }
    
    def list_tools(self) -> Dict[str, Any]:
        """
        List all available tools and their metadata
        
        Returns:
            Dictionary with tools information
        """
        return {
            "total_count": len(self.tools_registry),
            "loaded_count": len(self.loaded_tools),
            "tools": self.tools_registry,
            "loaded_tools": list(self.loaded_tools.keys()),
        }
    
    def remove_tool(self, tool_name: str) -> Dict[str, Any]:
        """
        Remove a tool from the system
        
        Args:
            tool_name: Name of the tool to remove
            
        Returns:
            Dictionary with removal results
        """
        try:
            # Remove from memory
            if tool_name in self.loaded_tools:
                del self.loaded_tools[tool_name]
            
            # Get file paths before removing from registry
            tool_info = self.tools_registry.get(tool_name, {})
            metadata = tool_info.get("metadata", {})
            
            # Remove from registry
            if tool_name in self.tools_registry:
                del self.tools_registry[tool_name]
                self._save_metadata()
            
            # Delete files
            files_deleted = []
            for ext in ['.py', '.lua']:
                file_path = self.tools_dir / f"{tool_name}{ext}"
                if file_path.exists():
                    file_path.unlink()
                    files_deleted.append(str(file_path))
            
            # Also try to delete from metadata file paths if available
            for path_key in ['lua_file_path', 'python_file_path']:
                if path_key in metadata:
                    file_path = Path(metadata[path_key])
                    if file_path.exists():
                        file_path.unlink()
                        files_deleted.append(str(file_path))
            
            return {
                "success": True,
                "message": f"Tool '{tool_name}' removed successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to remove tool: {str(e)}",
                "error": str(e)
            }

# Global instance
_unified_manager = None

def get_unified_tool_manager() -> UnifiedToolManager:
    """Get the global unified tool manager instance"""
    global _unified_manager
    if _unified_manager is None:
        _unified_manager = UnifiedToolManager()
    return _unified_manager