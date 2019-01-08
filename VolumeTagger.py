import boto3
import logging
import json
import sys
import argparse


class VolumeTagger:
    def __init__(self, unattached_tag_key='', unattached_tag_value='', whitelist_tags='', blacklist_tags='',
                 level='INFO'):
        logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
        self.mod_log = logging.getLogger('vol_tagger')
        log_level = logging.getLevelName(level.upper())
        self.mod_log.setLevel(log_level)

        if whitelist_tags and blacklist_tags:
            print('Error: Both a blacklist and a whitelist cannot be provided. Please choose one or the other.')
            sys.exit(1)

        self.whitelist_tags = whitelist_tags.split(',') if whitelist_tags else ''
        self.blacklist_tags = blacklist_tags.split(',') if blacklist_tags else ''

        continue_prompt = False

        name_overwrite_msg = 'This means that if an instance has the "Name" tag set, the volume\'s existing ' \
                             '"Name" tag will be overwritten.'

        if not self.blacklist_tags and not self.whitelist_tags:
            print(f'WARNING: No tag blacklist or whitelist provided. All tags will be copied from the attached EC2 '
                  f'instance where possible. {name_overwrite_msg}')

            continue_prompt = True

        elif self.blacklist_tags and 'Name' not in self.blacklist_tags:
            print(f'WARNING: "Name" tag is not in the blacklist. {name_overwrite_msg}')

            continue_prompt = True

        elif self.whitelist_tags and 'Name' in self.whitelist_tags:
            print(f'WARNING: "Name" tag is in the whitelist. {name_overwrite_msg}')

            continue_prompt = True

        while continue_prompt:
            response = input('Do you want to continue? (Y/N): ')
            if response.upper() == 'Y':
                break

            elif response.upper() == 'N':
                sys.exit()

        if not unattached_tag_key or not unattached_tag_value:
            self.mod_log.info('Unattached tag key and/or value not provided. Volumes which are not attached to an '
                              'instance will not be tagged.')

        self.mod_log.info('Creating boto3 EC2 client.')
        self.ec2_client = boto3.resource('ec2')

        self.instance_tag_mapping = self._instance_tag_map()
        self.tag_volumes(unattached_tag_key, unattached_tag_value)

    def _tag_check(self, tags):
        approved_tags = []

        self.mod_log.debug('Running tags through whitelist/blacklist filter.')
        for entry in tags:
            if self.whitelist_tags:
                if entry['Key'] in self.whitelist_tags:
                    self.mod_log.debug(f'Found whitelisted tag: {entry}')

                else:
                    continue

            if entry['Key'] in self.blacklist_tags:
                self.mod_log.debug(f'Found blacklisted tag: {entry}')
                continue

            approved_tags.append(entry)

        self.mod_log.debug(f'Approved tag list for this instance: {approved_tags}')
        return approved_tags

    def _instance_tag_map(self):
        instance_tag_mapping = dict()

        self.mod_log.info('Retrieving all EC2 instance details...')
        all_instances = self.ec2_client.instances.all()
        for instance in all_instances:
            instance_id = instance.instance_id
            tags = instance.tags

            self.mod_log.debug(f'Found Instance ID: {instance_id} with the following tags: {tags}')

            if self.whitelist_tags or self.blacklist_tags:
                approved_tags = self._tag_check(tags)

            else:
                approved_tags = tags

            instance_tag_mapping[instance_id] = approved_tags

        self.mod_log.debug(f'Finished retrieving EC2 instances and approved tags: {json.dumps(instance_tag_mapping)}')
        return instance_tag_mapping

    def tag_volumes(self, unattached_tag_key, unattached_tag_value):
        self.mod_log.info('Retrieving all volumes...')
        all_volumes = self.ec2_client.volumes.all()

        self.mod_log.info('Tagging volumes...')
        for volume in all_volumes:
            volume_id = volume.id
            self.mod_log.debug(f'Found Volume ID: {volume_id}')

            attached = volume.attachments
            if attached:
                for volume_info in attached:
                    instance_id = volume_info['InstanceId']
                    instance_tags = self.instance_tag_mapping[instance_id]
                    if not instance_tags:
                        self.mod_log.info(f'Volume is attached to Instance ID {instance_id} which has no tags, or all '
                                          f'of its tags are blacklisted, or none of its tags are whitelisted.')

                        continue

                    self.mod_log.debug(f'Volume is attached to Instance ID {instance_id} which has the following '
                                       f'approved tags: {instance_tags}')
                    volume.create_tags(Tags=instance_tags)
                    self.mod_log.debug(f'Attached tags to volume')

            elif unattached_tag_key and unattached_tag_value:
                self.mod_log.debug(f'Volume is not attached to an instance. Setting tag "{unattached_tag_key}" '
                                   f'to "{unattached_tag_value}"')

                unattached_tag = [
                    {
                        'Key': unattached_tag_key,
                        'Value': unattached_tag_value,
                    }
                ]

                volume.create_tags(Tags=unattached_tag)

            else:
                self.mod_log.debug('Volume is not attached to an instance. Leaving tags as is.')

        self.mod_log.info('Done.')

def main():
    parser = argparse.ArgumentParser(description='Add tags to unattached and/or volumes attached to EC2 instances')
    parser.add_argument('-b', '--blacklist_tags', type=str, help='Comma separated tag values')
    parser.add_argument('-w', '--whitelist_tags', type=str, help='Comma separated tag values')
    parser.add_argument('-k', '--unattached_tag_key', type=str, help='Tag key for unattached volumes')
    parser.add_argument('-v', '--unattached_tag_value', type=str, help='Tag value for unattached volumes')
    parser.add_argument('-l', '--log_level', default='INFO', type=str, help='Log level - DEBUG or INFO')
    args = parser.parse_args()

    VolumeTagger(unattached_tag_key=args.unattached_tag_key, unattached_tag_value=args.unattached_tag_value,
                 whitelist_tags=args.whitelist_tags, blacklist_tags=args.blacklist_tags, level=args.log_level)


if __name__ == '__main__':
    main()
