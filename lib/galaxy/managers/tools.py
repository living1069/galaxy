import logging
from uuid import uuid4

from galaxy import exceptions
from galaxy import model
from galaxy.exceptions import DuplicatedIdentifierException
from .base import ModelManager

log = logging.getLogger(__name__)


class DynamicToolManager(ModelManager):
    """ Manages dynamic tools stored in Galaxy's database.
    """
    model_class = model.DynamicTool

    def __init__(self, app):
        super(DynamicToolManager, self).__init__(app)

    def get_tool_by_uuid(self, uuid):
        dynamic_tool = self._one_or_none(
            self.query().filter(self.model_class.uuid == uuid)
        )
        return dynamic_tool

    def get_tool_by_tool_id(self, tool_id):
        dynamic_tool = self._one_or_none(
            self.query().filter(self.model_class.tool_id == tool_id)
        )
        return dynamic_tool

    def get_tool_by_id(self, object_id):
        dynamic_tool = self._one_or_none(
            self.query().filter(self.model_class.id == object_id)
        )
        return dynamic_tool

    def create_tool(self, tool_payload, allow_load=False):
        if "representation" not in tool_payload:
            raise exceptions.ObjectAttributeMissingException(
                "A tool 'representation' is required."
            )

        representation = tool_payload["representation"]
        if "class" not in representation:
            raise exceptions.ObjectAttributeMissingException(
                "Current tool representations require 'class'."
            )

        enable_beta_formats = getattr(self.app.config, "enable_beta_tool_formats", False)
        if not enable_beta_formats:
            raise exceptions.ConfigDoesNotAllowException("Set 'enable_beta_tool_formats' in Galaxy config to create dynamic tools.")

        tool_format = representation["class"]
        if tool_format == "GalaxyTool":
            uuid = tool_payload.get("uuid", None)
            if uuid is None:
                uuid = uuid4()

            tool_id = representation.get("id", None)
            if tool_id is None:
                tool_id = str(uuid)

            tool_version = representation.get("version", None)
            value = representation
        else:
            raise Exception("Unknown tool type encountered.")
        # TODO: enforce via DB constraint and catch appropriate
        # exception.
        existing_tool = self.get_tool_by_uuid(uuid)
        if existing_tool is not None and not allow_load:
            raise DuplicatedIdentifierException(existing_tool.id)
        elif existing_tool:
            dynamic_tool = existing_tool
        else:
            dynamic_tool = self.create(
                tool_format=tool_format,
                tool_id=tool_id,
                tool_version=tool_version,
                uuid=uuid,
                value=value,
            )
        self.app.toolbox.load_dynamic_tool(dynamic_tool)
        return dynamic_tool

    def list_tools(self, active=True):
        return self.query().filter(self.model_class.active == active)

    def deactivate(self, dynamic_tool):
        self.update(dynamic_tool, {"active": False})
        return dynamic_tool
