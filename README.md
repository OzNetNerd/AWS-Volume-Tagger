# AWS Volume Tagger (AVT)
## Alpha Code

**Note:** This code is still in the Alpha stage. Please test it before using it in a production environment.

## Intro

A simple script which is capable of doing the following:
1. Inherit tags from an attached instance. An optional user-defined blacklist or whitelist can be used to control 
which tags are used
2. Tag volumes which are not attached to an instance with a user-defined Key/Value pair

## Example

In this example we see the following:
* Logging level is set to DEBUG. This provides us with detailed information
* `Name` and `Department` tags are blacklisted. This means that if a volume is attached to an instance with either of
these tags, the volume WILL NOT inherit them. However, it will inherit all other tags
* Volumes which are not attached to an instance have their `Name` tag set to `UnattachedVolume`

```
$ python3 VolumeTagger.py -l debug -b Name,Department -k Name -v UnattachedVolume
08-Jan-19 23:46:23 - Creating boto3 EC2 client.
08-Jan-19 23:46:23 - Retrieving all EC2 instance details...
08-Jan-19 23:46:23 - Found Instance ID: i-0155363e62e1ee270 with the following tags: [{'Key': 'CostCentre', 'Value': '123'}, {'Key': 'Name', 'Value': 'AppServer'}, {'Key': 'Department', 'Value': 'IT'}]
08-Jan-19 23:46:23 - Running tags through whitelist/blacklist filter.
08-Jan-19 23:46:23 - Found blacklisted tag: {'Key': 'Name', 'Value': 'AppServer'}
08-Jan-19 23:46:23 - Found blacklisted tag: {'Key': 'Department', 'Value': 'IT'}
08-Jan-19 23:46:23 - Approved tag list for this instance: [{'Key': 'CostCentre', 'Value': '123'}]
08-Jan-19 23:46:23 - Found Instance ID: i-09f3f5341111176a5 with the following tags: [{'Key': 'Owner', 'Value': 'John'}, {'Key': 'Name', 'Value': 'WebServer'}]
08-Jan-19 23:46:23 - Running tags through whitelist/blacklist filter.
08-Jan-19 23:46:23 - Found blacklisted tag: {'Key': 'Name', 'Value': 'WebServer'}
08-Jan-19 23:46:23 - Approved tag list for this instance: [{'Key': 'Owner', 'Value': 'John'}]
08-Jan-19 23:46:23 - Finished retrieving EC2 instances and approved tags: {"i-0155363e62e1ee270": [{"Key": "CostCentre", "Value": "123"}], "i-09f3f5341111176a5": [{"Key": "Owner", "Value": "John"}]}
08-Jan-19 23:46:23 - Retrieving all volumes...
08-Jan-19 23:46:23 - Tagging volumes...
08-Jan-19 23:46:23 - Found Volume ID: vol-06bab127b46f40d15
08-Jan-19 23:46:23 - Volume is not attached to an instance. Setting tag "Name" to "UnattachedVolume"
08-Jan-19 23:46:23 - Found Volume ID: vol-09dcb414fd4f9254d
08-Jan-19 23:46:23 - Volume is not attached to an instance. Setting tag "Name" to "UnattachedVolume"
08-Jan-19 23:46:23 - Found Volume ID: vol-0222ac8f234290f41
08-Jan-19 23:46:23 - Volume is attached to Instance ID i-0155363e62e1ee270 which has the following approved tags: [{'Key': 'CostCentre', 'Value': '123'}]
08-Jan-19 23:46:24 - Attached tags to volume
08-Jan-19 23:46:24 - Found Volume ID: vol-0b5f83341c327a617
08-Jan-19 23:46:24 - Volume is attached to Instance ID i-09f3f5341111176a5 which has the following approved tags: [{'Key': 'Owner', 'Value': 'John'}]
08-Jan-19 23:46:24 - Attached tags to volume
08-Jan-19 23:46:24 - Done.
```

## Usage 

```
$ python3 VolumeTagger.py -h
usage: VolumeTagger.py [-h] [-b BLACKLIST_TAGS] [-w WHITELIST_TAGS]
                       [-k UNATTACHED_TAG_KEY] [-v UNATTACHED_TAG_VALUE]
                       [-l LOG_LEVEL]

Add tags to unattached and/or volumes attached to EC2 instances

optional arguments:
  -h, --help            show this help message and exit
  -b BLACKLIST_TAGS, --blacklist_tags BLACKLIST_TAGS
                        Comma separated tag values
  -w WHITELIST_TAGS, --whitelist_tags WHITELIST_TAGS
                        Comma separated tag values
  -k UNATTACHED_TAG_KEY, --unattached_tag_key UNATTACHED_TAG_KEY
                        Tag key for unattached volumes
  -v UNATTACHED_TAG_VALUE, --unattached_tag_value UNATTACHED_TAG_VALUE
                        Tag value for unattached volumes
  -l LOG_LEVEL, --log_level LOG_LEVEL
                        Log level - DEBUG or INFO
```

Each of the above flags are explained below. Note that they can be used in conjunction to achieve the desired result.

e.g `WHITELIST_TAGS` can be specified alongside the `UNATTACHED_TAG_KEY` and `UNATTACHED_TAG_VALUE` flags.

### No Arguments

```
$ python3 VolumeTagger.py
```

Running the script without any arguments will result in the following:
* A "Name" tag warning will be displayed. (See the '"Name" Tag Overwrite Warning' section below for more information.) 
* Unattached volumes which are attached to EC2 instances will inherit ALL tags from the EC2 instance. Existing volume
tags will be overwritten by the EC2 tags if there is an overlap. Non-overlapping tags will be left intact.
* Unattached volumes which ARE NOT attached to an EC2 instance will be left untouched.

### --unattached_tag_key (-k) --unattached_tag_value (-v)

```
$ python3 VolumeTagger.py -k <TagKey> -v <TagVlaue>
```

Running the script with the `-k` and `-v` argument will result in the following:
* A "Name" tag warning will be displayed. (See the '"Name" Tag Overwrite Warning' section below for more information.) 
* Unattached volumes which are attached to EC2 instances will inherit ALL tags from the EC2 instance. Existing volume
tags will be overwritten by the EC2 tags if there is an overlap. Non-overlapping tags will be left intact.
* Unattached volumes which ARE NOT attached to an EC2 instance will be tagged with the `TagKey` set to `TagValue`.
 
### --blacklist_tags (-b)

```
$ python3 VolumeTagger.py -b <TagKey1>,<TagKey2>,<TagKey3>
```

Running the script with the `-b` argument will result in the following:
* A "Name" tag warning will be displayed if `Name` is not specified. (See the '"Name" Tag Overwrite Warning' section 
below for more information.)
* Unattached volumes which are attached to EC2 instances will inherit **non-blacklisted** tags from the EC2 instance. 
Existing volume tags will be overwritten by the EC2 tags if there is an overlap. Non-overlapping tags will be left 
intact.
* Unattached volumes which ARE NOT attached to an EC2 instance will be left untouched.

### --whitelist_tags (-w)

```
$ python3 VolumeTagger.py -w <TagKey1>,<TagKey2>,<TagKey3>
```

Running the script with the `-w` argument will result in the following:
* A "Name" tag warning will be displayed if `Name` is specified. (See the '"Name" Tag Overwrite Warning' section 
below for more information.)
* Unattached volumes which are attached to EC2 instances will inherit **whitelisted** tags from the EC2 instance. 
Existing volume tags will be overwritten by the EC2 tags if there is an overlap. Non-overlapping tags will be left 
intact.
* Unattached volumes which ARE NOT attached to an EC2 instance will be left untouched.

### --log_level (-l)

```
$ python3 VolumeTagger.py -l <INFO | DEBUG>
```


Sets the logging level. Default is `INFO`.

## "Name" Tag Overwrite Warning Message

You will see the "Name" tag overwrite warning message unless you specify `Name` in a blacklist, or you do not specify
`Name` in a whitelist. This warning message is a safeguard to ensure you do not accidentally overwrite the volume's 
`Name` tag with that of the EC2 instance's.

If however, this is desired, you can respond to the warning with `Y` to proceed. 