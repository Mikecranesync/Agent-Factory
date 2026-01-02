"""
FactoryIOReadWriteTool - Read/write tag values.

Usage:
    tool = FactoryIOReadWriteTool()
    # Read single tag by name
    result = tool._run(action="read", tag_names=["Conveyor"])
    # Write single tag by name
    result = tool._run(action="write", tag_values={"Conveyor": True})
    # Read multiple tags
    result = tool._run(action="read", tag_names=["Conveyor", "Sensor"])
"""

from typing import Optional, Dict, List, Type, ClassVar, Any
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import requests
import json
import os


class FactoryIOReadWriteInput(BaseModel):
    """Input schema for FactoryIOReadWriteTool."""
    action: str = Field(
        description="Action: 'read', 'write', 'force', or 'release'"
    )
    tag_names: Optional[List[str]] = Field(
        default=None,
        description="List of tag names to read (for 'read' action) or release (for 'release' action)"
    )
    tag_values: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dict of tag_name: value to write (for 'write' action) or force (for 'force' action). Values can be bool (Bit), int (Int), or float (Float)"
    )


class FactoryIOReadWriteTool(BaseTool):
    """Read or write Factory.io tag values."""

    name: ClassVar[str] = "factoryio_readwrite"
    description: ClassVar[str] = """
    Read, write, force, or release Factory.io tag values.

    Actions:
    - read: Read current values of specified tags (by name)
    - write: Write values to specified tags (by name)
    - force: Force tags to specific values (HMI manual control, bypasses PLC logic)
    - release: Release forced tags back to normal operation

    Returns JSON with tag values or operation confirmation.

    Important: Tags must be referenced by name. Use FactoryIOTagTool to discover available tag names first.
    """
    args_schema: Type[BaseModel] = FactoryIOReadWriteInput

    base_url: str = os.getenv("FACTORY_IO_URL", "http://localhost:7410")
    timeout: int = int(os.getenv("FACTORY_IO_TIMEOUT", "5"))

    def _run(
        self,
        action: str,
        tag_names: Optional[List[str]] = None,
        tag_values: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute read/write/force/release action."""
        try:
            if action == "read":
                if not tag_names:
                    return "ERROR: tag_names required for 'read' action"
                return self._read_tags(tag_names)
            elif action == "write":
                if not tag_values:
                    return "ERROR: tag_values required for 'write' action"
                return self._write_tags(tag_values)
            elif action == "force":
                if not tag_values:
                    return "ERROR: tag_values required for 'force' action"
                return self._force_tags(tag_values)
            elif action == "release":
                if not tag_names:
                    return "ERROR: tag_names required for 'release' action"
                return self._release_tags(tag_names)
            else:
                return f"ERROR: Unknown action '{action}'. Valid actions: read, write, force, release"
        except requests.exceptions.ConnectionError:
            return f"ERROR: Cannot connect to Factory.io at {self.base_url}"
        except Exception as e:
            return f"ERROR: {str(e)}"

    def _read_tags(self, tag_names: List[str]) -> str:
        """Read current values of tags by name."""
        # Factory.io Web API uses /api/tag/values/by-name for reading by name
        response = requests.get(
            f"{self.base_url}/api/tag/values/by-name",
            json=tag_names,  # Send tag names in body
            timeout=self.timeout
        )
        response.raise_for_status()
        values = response.json()

        # Check for errors in response
        errors = []
        results = {}
        for item in values:
            if "error" in item:
                errors.append(f"{item.get('name', 'unknown')}: {item['error']}")
            else:
                results[item["name"]] = item["value"]

        # Format response
        if errors:
            return json.dumps({
                "success": False,
                "values": results,
                "errors": errors
            }, indent=2)
        else:
            return json.dumps({
                "success": True,
                "values": results
            }, indent=2)

    def _write_tags(self, tag_values: Dict[str, Any]) -> str:
        """Write values to tags by name."""
        # Convert dict to list of {name, value} objects for API
        tag_value_list = [
            {"name": name, "value": value}
            for name, value in tag_values.items()
        ]

        # Factory.io Web API uses /api/tag/values/by-name for writing by name
        response = requests.put(
            f"{self.base_url}/api/tag/values/by-name",
            json=tag_value_list,
            timeout=self.timeout
        )
        response.raise_for_status()
        result = response.json()

        # Check for errors in response
        errors = []
        if result:  # API returns array of errors (empty if all success)
            for item in result:
                if "error" in item:
                    errors.append(f"{item.get('name', 'unknown')}: {item['error']}")

        if errors:
            return json.dumps({
                "success": False,
                "message": f"Failed to write {len(errors)} tag(s)",
                "written": len(tag_values) - len(errors),
                "errors": errors
            }, indent=2)
        else:
            return json.dumps({
                "success": True,
                "message": f"Successfully wrote {len(tag_values)} tag value(s)",
                "tags": list(tag_values.keys())
            }, indent=2)

    def _force_tags(self, tag_values: Dict[str, Any]) -> str:
        """Force tag values using Factory.io native force API.

        Forces tags to specific values bypassing PLC logic. Useful for HMI
        manual control when no PLC logic is running.

        Args:
            tag_values: Dict mapping tag name to forced value

        Returns:
            JSON result with success status and forced tags
        """
        # Convert dict to list of {name, value} objects for API
        tag_value_list = [
            {"name": name, "value": value}
            for name, value in tag_values.items()
        ]

        # Factory.io Web API uses /api/tag/values-force/by-name for forcing by name
        response = requests.put(
            f"{self.base_url}/api/tag/values-force/by-name",
            json=tag_value_list,
            timeout=self.timeout
        )
        response.raise_for_status()
        result = response.json()

        # Check for errors in response
        errors = []
        if result:  # API returns array of errors (empty if all success)
            for item in result:
                if "error" in item:
                    errors.append(f"{item.get('name', 'unknown')}: {item['error']}")

        if errors:
            return json.dumps({
                "success": False,
                "message": f"Failed to force {len(errors)} tag(s)",
                "forced": len(tag_values) - len(errors),
                "errors": errors
            }, indent=2)
        else:
            return json.dumps({
                "success": True,
                "message": f"Successfully forced {len(tag_values)} tag value(s)",
                "tags": list(tag_values.keys())
            }, indent=2)

    def _release_tags(self, tag_names: List[str]) -> str:
        """Release forced tags using Factory.io native release API.

        Releases tags from forced state back to normal operation. All specified
        tags will return to their actual values determined by PLC logic or inputs.

        Args:
            tag_names: List of tag names to release from forced state

        Returns:
            JSON result with success status and released tags
        """
        # Factory.io Web API uses /api/tag/values-release/by-name for releasing by name
        response = requests.put(
            f"{self.base_url}/api/tag/values-release/by-name",
            json=tag_names,
            timeout=self.timeout
        )
        response.raise_for_status()
        result = response.json()

        # Check for errors in response
        errors = []
        if result:  # API returns array of errors (empty if all success)
            for item in result:
                if "error" in item:
                    errors.append(f"{item.get('name', 'unknown')}: {item['error']}")

        if errors:
            return json.dumps({
                "success": False,
                "message": f"Failed to release {len(errors)} tag(s)",
                "released": len(tag_names) - len(errors),
                "errors": errors
            }, indent=2)
        else:
            return json.dumps({
                "success": True,
                "message": f"Successfully released {len(tag_names)} tag(s)",
                "tags": tag_names
            }, indent=2)
