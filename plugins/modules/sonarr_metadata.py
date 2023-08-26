#!/usr/bin/python

# Copyright: (c) 2020, Fuochi <devopsarr@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: sonarr_metadata

short_description: Manages Sonarr metadata.

version_added: "1.0.0"

description: Manages Sonarr metadata.

options:
    name:
        description: Name.
        required: true
        type: str
    enable:
        description: enable flag.
        type: bool
        default: false

extends_documentation_fragment:
    - devopsarr.sonarr.sonarr_credentials
    - devopsarr.sonarr.sonarr_implementation
    - devopsarr.sonarr.sonarr_taggable
    - devopsarr.sonarr.sonarr_state

author:
    - Fuochi (@Fuochi)
'''

EXAMPLES = r'''
---
# Create a metadata
- name: Create a metadata
  devopsarr.sonarr.sonarr_metadata:
    name: "Example"
    enable: true
    config_contract: "WdtvMetadataSettings"
    implementation: "WdtvMetadata"
    fields:
    - name: "seasonImages"
      value: true
    tags: [1,2]

# Delete a metadata
- name: Delete a metadata
  devopsarr.sonarr.sonarr_metadata:
    name: Example
    state: absent
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
id:
    description: metadata ID.
    type: int
    returned: always
    sample: 1
name:
    description: Name.
    returned: always
    type: str
    sample: "Example"
enable:
    description: On grab flag.
    returned: always
    type: bool
    sample: true
config_contract:
    description: Config contract.
    returned: always
    type: str
    sample: "WebhookSettings"
implementation:
    description: Implementation.
    returned: always
    type: str
    sample: "Webhook"
tags:
    description: Tag list.
    type: list
    returned: always
    elements: int
    sample: [1,2]
fields:
    description: field list.
    type: list
    returned: always
'''

from ansible_collections.devopsarr.sonarr.plugins.module_utils.sonarr_module import SonarrModule
from ansible_collections.devopsarr.sonarr.plugins.module_utils.sonarr_field_utils import FieldHelper
from ansible.module_utils.common.text.converters import to_native

try:
    import sonarr
    HAS_SONARR_LIBRARY = True
except ImportError:
    HAS_SONARR_LIBRARY = False


def is_changed(status, want):
    if (want.name != status.name or
            want.enable != status.enable or
            want.config_contract != status.config_contract or
            want.implementation != status.implementation or
            want.tags != status.tags):
        return True

    for status_field in status.fields:
        for want_field in want.fields:
            if want_field.name == status_field.name and want_field.value != status_field.value:
                return True
    return False


def run_module():
    field_helper = FieldHelper()

    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', required=True),
        enable=dict(type='bool', default=False),
        config_contract=dict(type='str'),
        implementation=dict(type='str'),
        tags=dict(type='list', elements='int', default=[]),
        fields=dict(type='list', elements='dict', options=field_helper.field_args),
        state=dict(default='present', type='str', choices=['present', 'absent']),
    )

    result = dict(
        changed=False,
        id=0,
    )

    module = SonarrModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    client = sonarr.MetadataApi(module.api)

    # List resources.
    try:
        metadatas = client.list_metadata()
    except Exception as e:
        module.fail_json('Error listing metadatas: %s' % to_native(e.reason), **result)

    state = sonarr.MetadataResource()
    # Check if a resource is present already.
    for metadata in metadatas:
        if metadata['name'] == module.params['name']:
            result.update(metadata.dict(by_alias=False))
            state = metadata

    # Delete the resource if needed.
    if module.params['state'] == 'absent':
        if result['id'] != 0:
            result['changed'] = True
            if not module.check_mode:
                try:
                    response = client.delete_metadata(result['id'])
                except Exception as e:
                    module.fail_json('Error deleting metadata: %s' % to_native(e.reason), **result)
                result['id'] = 0
        module.exit_json(**result)

    want = sonarr.MetadataResource(**{
        'name': module.params['name'],
        'enable': module.params['enable'],
        'config_contract': module.params['config_contract'],
        'implementation': module.params['implementation'],
        'tags': module.params['tags'],
        'fields': field_helper.populate_fields(module.params['fields']),
    })

    # Create a new resource.
    if result['id'] == 0:
        result['changed'] = True
        # Only without check mode.
        if not module.check_mode:
            try:
                response = client.create_metadata(metadata_resource=want)
            except Exception as e:
                module.fail_json('Error creating metadata: %s' % to_native(e.reason), **result)
            result.update(response.dict(by_alias=False))
        module.exit_json(**result)

    # Update an existing resource.
    want.id = result['id']
    if is_changed(state, want):
        result['changed'] = True
        if not module.check_mode:
            try:
                response = client.update_metadata(metadata_resource=want, id=str(want.id))
            except Exception as e:
                module.fail_json('Error updating metadata: %s' % to_native(e.reason), **result)
        result.update(response.dict(by_alias=False))

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()