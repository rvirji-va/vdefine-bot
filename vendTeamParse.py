# coding: utf-8
import json
import re
import urllib2
from string import lower

from BeautifulSoup import BeautifulSoup


def iterate_members(member_file, rescrape=False, write_changes=False):

    if rescrape:
        response = urllib2.urlopen('https://www.vendasta.com/company/team')
        html = response.read()
        soup = BeautifulSoup(html)
        ul = soup.find('ul', id='team')
        if write_changes:
            f = open(member_file, 'w+')
            f.write(''.join(map(str, ul.contents)))

    member_data = open(member_file).read().replace('\n', '')
    member_data = re.sub('[\s]{2,}', ' ', member_data)
    member_list = member_data.split('</li>')
    for member in member_list:
        if write_changes:
            write_JSON(convert_member_to_dict(member))


def write_JSON(dict):
    #print dict
    if dict.get('id', False):
        f = open('/db/users/' + dict['id'] + '.json', 'w+')
        f.write(json.dumps(dict))


def convert_member_to_dict(member):
    person = {}
    t_index = member.find('class="mix') + 15  # Member Type
    if member.find("exe\">") > -1:
        p_type = 'exe'
        person["type"] = get_type_from_code(p_type)
    elif t_index > 14:
        p_type = member[t_index:t_index + 3]
        person["type"] = get_type_from_code(p_type)
    i_index = member.find("<img src=") + 10  # Member Image
    if i_index > 9:
        alt = member.find("alt=")+5
        person["name"] = member[alt:alt+(member[alt:].find('" />'))]
        person["slack"] = get_slack_name(person["name"])
        person["id"] = lower(person["name"]).replace(' ', '')
    b_index = member.find("<p><strong>") + 11  # Member Bio
    if b_index > 10:
        bio = member[b_index:member.find('</p>')]
        # the following filters out non-ascii characters
        # I blame the hangover
        # http://stackoverflow.com/questions/1342000/how-to-make-the-python-interpreter-correctly-handle-non-ascii-characters-in-stri
        person["bio"] = "".join(i for i in extract_bio(bio) if ord(i) < 128)
    print person
    return person


def extract_bio(bio):
    bio = bio.replace('</strong>', '')
    end_index = bio.find("<span")
    if end_index > -1:
        return bio[:end_index]
    else:
        return bio


def get_slack_name(name):
    if len(name) < 1:
        return False
    names = name.split(" ")
    return "@{}{}".format(lower(names[0][0]), lower(names[len(names)-1]))


def get_type_from_code(p_type):
    return {
        'bop': "Biz Ops",
        'des': "Design",
        'dev': "Research and Development",
        'ful': "Digital Agency",
        'exe': "The Executive Department",
        'mar': "Marketing",
        'psc': "Partner Success",
        'pst': "Partner Support",
        'sal': "Sales",
        'sup': "Ops and Finance",

    }.get(p_type, "Crazy Person's Guild")


if __name__ == '__main__':
    iterate_members('vendasta_team.html', rescrape=True, write_changes=True)
