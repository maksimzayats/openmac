"""Common classes and commands for all applications."""
from __future__ import annotations

from pydantic import BaseModel

from openmac._internal import sdef

"""
<class name="application" code="capp" description="The application&apos;s top-level scripting object.">
      <cocoa class="BrowserCrApplication"/>
      <element description="The windows contained within this application, ordered front to back." type="window">
        <cocoa key="appleScriptWindows"/>
      </element>
      <property name="name" code="pnam" description="The name of the application." type="text" access="r"/>
      <property name="frontmost" code="pisf" description="Is this the frontmost (active) application?" type="boolean" access="r">
        <cocoa key="isActive"/>
      </property>
      <property name="version" code="vers" description="The version of the application." type="text" access="r"/>
      <responds-to command="open">
        <cocoa method="handleOpenScriptCommand:"/>
      </responds-to>
      <responds-to command="print">
        <cocoa method="handlePrintScriptCommand:"/>
      </responds-to>
      <responds-to command="quit">
        <cocoa method="handleQuitScriptCommand:"/>
      </responds-to>
    </class>
"""


class Application(BaseModel):
    name: sdef.Text
    """The name of the application."""
    frontmost: sdef.Boolean
    """Is this the frontmost (active) application?"""
    version: sdef.Text
    """The version of the application."""

    windows: Manager[Window]
