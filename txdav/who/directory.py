##
# Copyright (c) 2006-2014 Apple Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##

"""
Calendar/Contacts specific methods for DirectoryRecord
"""


import uuid


__all__ = [
    "CalendarDirectoryRecordMixin",
    "CalendarDirectoryServiceMixin",
]


class CalendarDirectoryServiceMixin(object):

    # Must maintain the hack for a bit longer:
    def setPrincipalCollection(self, principalCollection):
        """
        Set the principal service that the directory relies on for doing proxy tests.

        @param principalService: the principal service.
        @type principalService: L{DirectoryProvisioningResource}
        """
        self.principalCollection = principalCollection


class CalendarDirectoryRecordMixin(object):


    @property
    def calendarUserAddresses(self):
        if not self.hasCalendars:
            return frozenset()

        try:
            cuas = set(
                ["mailto:%s" % (emailAddress,)
                 for emailAddress in self.emailAddresses]
            )
        except AttributeError:
            cuas = set()

        try:
            if self.guid:
                if isinstance(self.guid, uuid.UUID):
                    guid = unicode(self.guid).upper()
                else:
                    guid = self.guid
                cuas.add("urn:uuid:{guid}".format(guid=guid))
        except AttributeError:
            # No guid
            pass
        cuas.add("/principals/__uids__/{uid}/".format(uid=self.uid))
        for shortName in self.shortNames:
            cuas.add("/principals/{rt}/{sn}/".format(
                rt=self.recordType.name + "s", sn=shortName)
            )
        return frozenset(cuas)


    def getCUType(self):
        # Mapping from directory record.recordType to RFC2445 CUTYPE values
        self._cuTypes = {
            self.service.recordType.user: 'INDIVIDUAL',
            self.service.recordType.group: 'GROUP',
            self.service.recordType.resource: 'RESOURCE',
            self.service.recordType.location: 'ROOM',
        }

        return self._cuTypes.get(self.recordType, "UNKNOWN")


    @property
    def displayName(self):
        return self.fullNames[0]


    def cacheToken(self):
        """
        Generate a token that can be uniquely used to identify the state of this record for use
        in a cache.
        """
        return hash((
            self.__class__.__name__,
            self.service.realmName,
            self.recordType.name,
            self.shortNames,
            self.guid,
            self.hasCalendars,
        ))


    def canonicalCalendarUserAddress(self):
        """
            Return a CUA for this record, preferring in this order:
            urn:uuid: form
            mailto: form
            first in calendarUserAddresses list
        """

        cua = ""
        for candidate in self.calendarUserAddresses:
            # Pick the first one, but urn:uuid: and mailto: can override
            if not cua:
                cua = candidate
            # But always immediately choose the urn:uuid: form
            if candidate.startswith("urn:uuid:"):
                cua = candidate
                break
            # Prefer mailto: if no urn:uuid:
            elif candidate.startswith("mailto:"):
                cua = candidate
        return cua


    def enabledAsOrganizer(self):
        # MOVE2WHO FIXME TO LOOK AT CONFIG
        if self.recordType == self.service.recordType.user:
            return True
        elif self.recordType == self.service.recordType.group:
            return False  # config.Scheduling.Options.AllowGroupAsOrganizer
        elif self.recordType == self.service.recordType.location:
            return False  # config.Scheduling.Options.AllowLocationAsOrganizer
        elif self.recordType == self.service.recordType.resource:
            return False  # config.Scheduling.Options.AllowResourceAsOrganizer
        else:
            return False


    #MOVE2WHO
    def thisServer(self):
        return True


    def isLoginEnabled(self):
        return self.loginAllowed


    #MOVE2WHO
    def calendarsEnabled(self):
        # In the old world, this *also* looked at config:
        # return config.EnableCalDAV and self.enabledForCalendaring
        return self.hasCalendars


    def getAutoScheduleMode(self, organizer):
        # MOVE2WHO Fix this to take organizer into account:
        return self.autoScheduleMode


    def canAutoSchedule(self, organizer=None):
        # MOVE2WHO Fix this:
        return True