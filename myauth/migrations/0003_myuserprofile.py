# Generated by Django 3.1.7 on 2025-02-28 09:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('myauth', '0002_auto_20210331_1045'),
    ]

    operations = [
        migrations.CreateModel(
            name='MyUserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timezone', models.CharField(choices=[('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), ('America/Barbados', 'America/Barbados'), ('Etc/GMT', 'Etc/GMT'), ('Asia/Saigon', 'Asia/Saigon'), ('Europe/Ulyanovsk', 'Europe/Ulyanovsk'), ('Asia/Kashgar', 'Asia/Kashgar'), ('Etc/GMT+12', 'Etc/GMT+12'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('Canada/Saskatchewan', 'Canada/Saskatchewan'), ('Asia/Almaty', 'Asia/Almaty'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('America/Dawson', 'America/Dawson'), ('Africa/Algiers', 'Africa/Algiers'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('ROK', 'ROK'), ('Antarctica/Davis', 'Antarctica/Davis'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('ROC', 'ROC'), ('Asia/Gaza', 'Asia/Gaza'), ('Asia/Oral', 'Asia/Oral'), ('America/Miquelon', 'America/Miquelon'), ('America/Shiprock', 'America/Shiprock'), ('Europe/Belfast', 'Europe/Belfast'), ('Pacific/Midway', 'Pacific/Midway'), ('Asia/Urumqi', 'Asia/Urumqi'), ('Asia/Bangkok', 'Asia/Bangkok'), ('Asia/Hebron', 'Asia/Hebron'), ('America/Recife', 'America/Recife'), ('Europe/Chisinau', 'Europe/Chisinau'), ('America/St_Johns', 'America/St_Johns'), ('America/Swift_Current', 'America/Swift_Current'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('America/Grenada', 'America/Grenada'), ('Africa/Bissau', 'Africa/Bissau'), ('Mexico/BajaSur', 'Mexico/BajaSur'), ('Australia/Canberra', 'Australia/Canberra'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('Antarctica/Troll', 'Antarctica/Troll'), ('Pacific/Kanton', 'Pacific/Kanton'), ('Africa/Kigali', 'Africa/Kigali'), ('America/Porto_Acre', 'America/Porto_Acre'), ('Etc/GMT+0', 'Etc/GMT+0'), ('America/Belize', 'America/Belize'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('America/Bahia', 'America/Bahia'), ('Australia/Yancowinna', 'Australia/Yancowinna'), ('America/Adak', 'America/Adak'), ('Asia/Colombo', 'Asia/Colombo'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('Etc/GMT-1', 'Etc/GMT-1'), ('America/New_York', 'America/New_York'), ('Etc/GMT+1', 'Etc/GMT+1'), ('Pacific/Ponape', 'Pacific/Ponape'), ('Etc/UTC', 'Etc/UTC'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('America/Cayman', 'America/Cayman'), ('Universal', 'Universal'), ('Australia/West', 'Australia/West'), ('Africa/Cairo', 'Africa/Cairo'), ('Asia/Atyrau', 'Asia/Atyrau'), ('UCT', 'UCT'), ('HST', 'HST'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'), ('Indian/Chagos', 'Indian/Chagos'), ('Asia/Riyadh', 'Asia/Riyadh'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('America/Managua', 'America/Managua'), ('MST7MDT', 'MST7MDT'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('Africa/Kampala', 'Africa/Kampala'), ('Etc/GMT-6', 'Etc/GMT-6'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('America/Asuncion', 'America/Asuncion'), ('Asia/Macao', 'Asia/Macao'), ('Africa/Dakar', 'Africa/Dakar'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('Poland', 'Poland'), ('America/Ojinaga', 'America/Ojinaga'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('Europe/Astrakhan', 'Europe/Astrakhan'), ('Europe/Budapest', 'Europe/Budapest'), ('Africa/Maputo', 'Africa/Maputo'), ('Europe/Tallinn', 'Europe/Tallinn'), ('US/Arizona', 'US/Arizona'), ('America/Mendoza', 'America/Mendoza'), ('GB-Eire', 'GB-Eire'), ('Atlantic/Azores', 'Atlantic/Azores'), ('NZ', 'NZ'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('Australia/Sydney', 'Australia/Sydney'), ('America/Menominee', 'America/Menominee'), ('EET', 'EET'), ('America/Nipigon', 'America/Nipigon'), ('Europe/Brussels', 'Europe/Brussels'), ('Japan', 'Japan'), ('America/Atikokan', 'America/Atikokan'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby'), ('America/Detroit', 'America/Detroit'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('America/El_Salvador', 'America/El_Salvador'), ('America/Metlakatla', 'America/Metlakatla'), ('Etc/UCT', 'Etc/UCT'), ('Asia/Pontianak', 'Asia/Pontianak'), ('Asia/Tashkent', 'Asia/Tashkent'), ('Africa/Asmara', 'Africa/Asmara'), ('America/Catamarca', 'America/Catamarca'), ('America/Araguaina', 'America/Araguaina'), ('Pacific/Gambier', 'Pacific/Gambier'), ('Europe/Vatican', 'Europe/Vatican'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('America/Antigua', 'America/Antigua'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('Asia/Anadyr', 'Asia/Anadyr'), ('America/Scoresbysund', 'America/Scoresbysund'), ('Australia/Darwin', 'Australia/Darwin'), ('Europe/Dublin', 'Europe/Dublin'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('Asia/Hovd', 'Asia/Hovd'), ('Asia/Tomsk', 'Asia/Tomsk'), ('Asia/Bahrain', 'Asia/Bahrain'), ('Indian/Mauritius', 'Indian/Mauritius'), ('Europe/Moscow', 'Europe/Moscow'), ('Brazil/East', 'Brazil/East'), ('Africa/Djibouti', 'Africa/Djibouti'), ('America/Rio_Branco', 'America/Rio_Branco'), ('America/Hermosillo', 'America/Hermosillo'), ('America/St_Thomas', 'America/St_Thomas'), ('America/Bogota', 'America/Bogota'), ('US/Central', 'US/Central'), ('Asia/Taipei', 'Asia/Taipei'), ('Etc/Universal', 'Etc/Universal'), ('Antarctica/South_Pole', 'Antarctica/South_Pole'), ('Canada/Mountain', 'Canada/Mountain'), ('America/Cayenne', 'America/Cayenne'), ('Asia/Seoul', 'Asia/Seoul'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('Etc/GMT+10', 'Etc/GMT+10'), ('America/Cordoba', 'America/Cordoba'), ('Africa/Tripoli', 'Africa/Tripoli'), ('Etc/GMT-5', 'Etc/GMT-5'), ('Africa/Bangui', 'Africa/Bangui'), ('America/Ciudad_Juarez', 'America/Ciudad_Juarez'), ('Indian/Maldives', 'Indian/Maldives'), ('America/Costa_Rica', 'America/Costa_Rica'), ('Etc/GMT+6', 'Etc/GMT+6'), ('Asia/Brunei', 'Asia/Brunei'), ('America/Mexico_City', 'America/Mexico_City'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('America/Eirunepe', 'America/Eirunepe'), ('Cuba', 'Cuba'), ('Asia/Makassar', 'Asia/Makassar'), ('Asia/Qostanay', 'Asia/Qostanay'), ('Europe/Istanbul', 'Europe/Istanbul'), ('America/Curacao', 'America/Curacao'), ('Pacific/Guam', 'Pacific/Guam'), ('US/Alaska', 'US/Alaska'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh'), ('Indian/Mahe', 'Indian/Mahe'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('America/Iqaluit', 'America/Iqaluit'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('Africa/Banjul', 'Africa/Banjul'), ('Europe/Belgrade', 'Europe/Belgrade'), ('America/Inuvik', 'America/Inuvik'), ('Asia/Dacca', 'Asia/Dacca'), ('Pacific/Chatham', 'Pacific/Chatham'), ('America/Rainy_River', 'America/Rainy_River'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('Etc/GMT-3', 'Etc/GMT-3'), ('America/Maceio', 'America/Maceio'), ('America/Santarem', 'America/Santarem'), ('America/Sitka', 'America/Sitka'), ('Asia/Barnaul', 'Asia/Barnaul'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('Brazil/West', 'Brazil/West'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('America/Santiago', 'America/Santiago'), ('Australia/Hobart', 'Australia/Hobart'), ('Africa/Gaborone', 'Africa/Gaborone'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('Brazil/DeNoronha', 'Brazil/DeNoronha'), ('Asia/Muscat', 'Asia/Muscat'), ('Etc/GMT+8', 'Etc/GMT+8'), ('Etc/GMT-14', 'Etc/GMT-14'), ('Pacific/Yap', 'Pacific/Yap'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('Asia/Yangon', 'Asia/Yangon'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('Chile/EasterIsland', 'Chile/EasterIsland'), ('Egypt', 'Egypt'), ('America/Rosario', 'America/Rosario'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('America/Jamaica', 'America/Jamaica'), ('Africa/Khartoum', 'Africa/Khartoum'), ('Europe/Nicosia', 'Europe/Nicosia'), ('America/Noronha', 'America/Noronha'), ('America/Matamoros', 'America/Matamoros'), ('Africa/Blantyre', 'Africa/Blantyre'), ('Africa/Juba', 'Africa/Juba'), ('Asia/Jakarta', 'Asia/Jakarta'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('America/Montreal', 'America/Montreal'), ('Asia/Kolkata', 'Asia/Kolkata'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('Asia/Qatar', 'Asia/Qatar'), ('Etc/GMT+11', 'Etc/GMT+11'), ('Australia/Victoria', 'Australia/Victoria'), ('Asia/Ulan_Bator', 'Asia/Ulan_Bator'), ('Africa/Libreville', 'Africa/Libreville'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('Asia/Tehran', 'Asia/Tehran'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('Asia/Macau', 'Asia/Macau'), ('America/Punta_Arenas', 'America/Punta_Arenas'), ('Antarctica/Casey', 'Antarctica/Casey'), ('Asia/Kuching', 'Asia/Kuching'), ('Europe/Lisbon', 'Europe/Lisbon'), ('Navajo', 'Navajo'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('Asia/Calcutta', 'Asia/Calcutta'), ('Etc/GMT-4', 'Etc/GMT-4'), ('Africa/Harare', 'Africa/Harare'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('Australia/NSW', 'Australia/NSW'), ('Singapore', 'Singapore'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('Asia/Ujung_Pandang', 'Asia/Ujung_Pandang'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('GB', 'GB'), ('America/Lima', 'America/Lima'), ('Etc/GMT+7', 'Etc/GMT+7'), ('America/Tijuana', 'America/Tijuana'), ('Asia/Thimbu', 'Asia/Thimbu'), ('Asia/Damascus', 'Asia/Damascus'), ('Asia/Harbin', 'Asia/Harbin'), ('Portugal', 'Portugal'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('Pacific/Apia', 'Pacific/Apia'), ('Indian/Christmas', 'Indian/Christmas'), ('Europe/Riga', 'Europe/Riga'), ('Europe/Andorra', 'Europe/Andorra'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('Africa/Lusaka', 'Africa/Lusaka'), ('Asia/Amman', 'Asia/Amman'), ('Etc/GMT-8', 'Etc/GMT-8'), ('Australia/North', 'Australia/North'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('America/Monterrey', 'America/Monterrey'), ('Factory', 'Factory'), ('America/Dominica', 'America/Dominica'), ('Indian/Reunion', 'Indian/Reunion'), ('Indian/Mayotte', 'Indian/Mayotte'), ('America/Nuuk', 'America/Nuuk'), ('America/Virgin', 'America/Virgin'), ('Etc/GMT-0', 'Etc/GMT-0'), ('Africa/Freetown', 'Africa/Freetown'), ('America/Paramaribo', 'America/Paramaribo'), ('Europe/Athens', 'Europe/Athens'), ('America/Buenos_Aires', 'America/Buenos_Aires'), ('Asia/Bishkek', 'Asia/Bishkek'), ('Etc/Zulu', 'Etc/Zulu'), ('America/Godthab', 'America/Godthab'), ('Asia/Tokyo', 'Asia/Tokyo'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('Eire', 'Eire'), ('Asia/Nicosia', 'Asia/Nicosia'), ('Europe/Kirov', 'Europe/Kirov'), ('Asia/Kuwait', 'Asia/Kuwait'), ('Asia/Vientiane', 'Asia/Vientiane'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('Asia/Manila', 'Asia/Manila'), ('Etc/GMT0', 'Etc/GMT0'), ('US/Indiana-Starke', 'US/Indiana-Starke'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('Asia/Ashkhabad', 'Asia/Ashkhabad'), ('Etc/GMT-11', 'Etc/GMT-11'), ('America/Vancouver', 'America/Vancouver'), ('W-SU', 'W-SU'), ('Asia/Shanghai', 'Asia/Shanghai'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('Asia/Rangoon', 'Asia/Rangoon'), ('America/Glace_Bay', 'America/Glace_Bay'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('Asia/Baghdad', 'Asia/Baghdad'), ('America/Mazatlan', 'America/Mazatlan'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('Pacific/Auckland', 'Pacific/Auckland'), ('America/Porto_Velho', 'America/Porto_Velho'), ('Europe/Jersey', 'Europe/Jersey'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('America/Thule', 'America/Thule'), ('US/Pacific', 'US/Pacific'), ('Atlantic/Stanley', 'Atlantic/Stanley'), ('Africa/Accra', 'Africa/Accra'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('Europe/Tirane', 'Europe/Tirane'), ('America/Knox_IN', 'America/Knox_IN'), ('Europe/Prague', 'Europe/Prague'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('Europe/Tiraspol', 'Europe/Tiraspol'), ('Africa/Tunis', 'Africa/Tunis'), ('Asia/Ashgabat', 'Asia/Ashgabat'), ('Asia/Karachi', 'Asia/Karachi'), ('Asia/Chongqing', 'Asia/Chongqing'), ('America/Fortaleza', 'America/Fortaleza'), ('Asia/Tel_Aviv', 'Asia/Tel_Aviv'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('Australia/Brisbane', 'Australia/Brisbane'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('Europe/Madrid', 'Europe/Madrid'), ('America/Campo_Grande', 'America/Campo_Grande'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('Etc/GMT+4', 'Etc/GMT+4'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('Pacific/Niue', 'Pacific/Niue'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('Pacific/Saipan', 'Pacific/Saipan'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('Australia/ACT', 'Australia/ACT'), ('Africa/Casablanca', 'Africa/Casablanca'), ('America/Nome', 'America/Nome'), ('Africa/Malabo', 'Africa/Malabo'), ('Asia/Dili', 'Asia/Dili'), ('Asia/Omsk', 'Asia/Omsk'), ('Atlantic/Canary', 'Atlantic/Canary'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('Asia/Dubai', 'Asia/Dubai'), ('Pacific/Fiji', 'Pacific/Fiji'), ('Asia/Dhaka', 'Asia/Dhaka'), ('America/Coral_Harbour', 'America/Coral_Harbour'), ('Asia/Thimphu', 'Asia/Thimphu'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('America/Marigot', 'America/Marigot'), ('America/Louisville', 'America/Louisville'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('America/Manaus', 'America/Manaus'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('GMT-0', 'GMT-0'), ('Europe/Monaco', 'Europe/Monaco'), ('Etc/GMT+2', 'Etc/GMT+2'), ('Europe/Volgograd', 'Europe/Volgograd'), ('Asia/Magadan', 'Asia/Magadan'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('CET', 'CET'), ('America/Creston', 'America/Creston'), ('Chile/Continental', 'Chile/Continental'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('Africa/Lagos', 'Africa/Lagos'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('America/Anguilla', 'America/Anguilla'), ('Pacific/Samoa', 'Pacific/Samoa'), ('Europe/Bratislava', 'Europe/Bratislava'), ('America/Lower_Princes', 'America/Lower_Princes'), ('Pacific/Palau', 'Pacific/Palau'), ('Africa/Nairobi', 'Africa/Nairobi'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('Mexico/BajaNorte', 'Mexico/BajaNorte'), ('Europe/San_Marino', 'Europe/San_Marino'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('MST', 'MST'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('US/East-Indiana', 'US/East-Indiana'), ('America/Caracas', 'America/Caracas'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('America/Atka', 'America/Atka'), ('America/Winnipeg', 'America/Winnipeg'), ('Europe/Vilnius', 'Europe/Vilnius'), ('Europe/Stockholm', 'Europe/Stockholm'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'), ('Europe/Minsk', 'Europe/Minsk'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('MET', 'MET'), ('Turkey', 'Turkey'), ('Asia/Baku', 'Asia/Baku'), ('Indian/Comoro', 'Indian/Comoro'), ('America/Martinique', 'America/Martinique'), ('Australia/Queensland', 'Australia/Queensland'), ('America/Chihuahua', 'America/Chihuahua'), ('Mexico/General', 'Mexico/General'), ('Europe/Saratov', 'Europe/Saratov'), ('Libya', 'Libya'), ('Asia/Katmandu', 'Asia/Katmandu'), ('Asia/Samarkand', 'Asia/Samarkand'), ('GMT', 'GMT'), ('Asia/Aden', 'Asia/Aden'), ('NZ-CHAT', 'NZ-CHAT'), ('Europe/Kyiv', 'Europe/Kyiv'), ('America/Belem', 'America/Belem'), ('Europe/Helsinki', 'Europe/Helsinki'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('Etc/GMT+3', 'Etc/GMT+3'), ('Canada/Atlantic', 'Canada/Atlantic'), ('US/Michigan', 'US/Michigan'), ('Pacific/Johnston', 'Pacific/Johnston'), ('PRC', 'PRC'), ('America/Ensenada', 'America/Ensenada'), ('Canada/Pacific', 'Canada/Pacific'), ('Africa/Timbuktu', 'Africa/Timbuktu'), ('Australia/Lindeman', 'Australia/Lindeman'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('America/Whitehorse', 'America/Whitehorse'), ('America/Jujuy', 'America/Jujuy'), ('Pacific/Nauru', 'Pacific/Nauru'), ('Etc/GMT+5', 'Etc/GMT+5'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('US/Hawaii', 'US/Hawaii'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('US/Samoa', 'US/Samoa'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('Pacific/Noumea', 'Pacific/Noumea'), ('America/Aruba', 'America/Aruba'), ('Africa/Windhoek', 'Africa/Windhoek'), ('America/Cancun', 'America/Cancun'), ('America/Phoenix', 'America/Phoenix'), ('Europe/Malta', 'Europe/Malta'), ('Africa/Maseru', 'Africa/Maseru'), ('Africa/Douala', 'Africa/Douala'), ('Africa/Monrovia', 'Africa/Monrovia'), ('Canada/Yukon', 'Canada/Yukon'), ('Etc/GMT-7', 'Etc/GMT-7'), ('Africa/Bamako', 'Africa/Bamako'), ('Pacific/Wallis', 'Pacific/Wallis'), ('Australia/Adelaide', 'Australia/Adelaide'), ('Asia/Yerevan', 'Asia/Yerevan'), ('Asia/Ust-Nera', 'Asia/Ust-Nera'), ('Australia/Melbourne', 'Australia/Melbourne'), ('Greenwich', 'Greenwich'), ('Zulu', 'Zulu'), ('America/Pangnirtung', 'America/Pangnirtung'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('Asia/Kabul', 'Asia/Kabul'), ('America/Fort_Wayne', 'America/Fort_Wayne'), ('Europe/Zagreb', 'Europe/Zagreb'), ('America/Guayaquil', 'America/Guayaquil'), ('America/Juneau', 'America/Juneau'), ('America/Los_Angeles', 'America/Los_Angeles'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('US/Eastern', 'US/Eastern'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('Brazil/Acre', 'Brazil/Acre'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('America/Yakutat', 'America/Yakutat'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('America/Boise', 'America/Boise'), ('Etc/GMT+9', 'Etc/GMT+9'), ('America/Montserrat', 'America/Montserrat'), ('Europe/Warsaw', 'Europe/Warsaw'), ('Etc/GMT-13', 'Etc/GMT-13'), ('Etc/Greenwich', 'Etc/Greenwich'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('Asia/Aqtau', 'Asia/Aqtau'), ('America/Grand_Turk', 'America/Grand_Turk'), ('America/Goose_Bay', 'America/Goose_Bay'), ('Europe/Vienna', 'Europe/Vienna'), ('Iceland', 'Iceland'), ('Africa/Mbabane', 'Africa/Mbabane'), ('US/Aleutian', 'US/Aleutian'), ('America/Guatemala', 'America/Guatemala'), ('Europe/Rome', 'Europe/Rome'), ('Asia/Jayapura', 'Asia/Jayapura'), ('Australia/South', 'Australia/South'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('Europe/Zurich', 'Europe/Zurich'), ('US/Mountain', 'US/Mountain'), ('WET', 'WET'), ('America/La_Paz', 'America/La_Paz'), ('Africa/Abidjan', 'Africa/Abidjan'), ('America/Toronto', 'America/Toronto'), ('America/Chicago', 'America/Chicago'), ('America/Denver', 'America/Denver'), ('CST6CDT', 'CST6CDT'), ('Africa/Luanda', 'Africa/Luanda'), ('America/Boa_Vista', 'America/Boa_Vista'), ('America/Nassau', 'America/Nassau'), ('Asia/Chungking', 'Asia/Chungking'), ('America/Resolute', 'America/Resolute'), ('Europe/Kiev', 'Europe/Kiev'), ('America/St_Kitts', 'America/St_Kitts'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('Europe/Paris', 'Europe/Paris'), ('Europe/Sofia', 'Europe/Sofia'), ('GMT+0', 'GMT+0'), ('America/Tortola', 'America/Tortola'), ('Atlantic/Jan_Mayen', 'Atlantic/Jan_Mayen'), ('Africa/Conakry', 'Africa/Conakry'), ('Hongkong', 'Hongkong'), ('Europe/Guernsey', 'Europe/Guernsey'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('Australia/Currie', 'Australia/Currie'), ('Pacific/Truk', 'Pacific/Truk'), ('Europe/Podgorica', 'Europe/Podgorica'), ('Africa/Asmera', 'Africa/Asmera'), ('Pacific/Wake', 'Pacific/Wake'), ('Pacific/Easter', 'Pacific/Easter'), ('Europe/London', 'Europe/London'), ('America/Havana', 'America/Havana'), ('Australia/Tasmania', 'Australia/Tasmania'), ('Australia/Eucla', 'Australia/Eucla'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('America/Halifax', 'America/Halifax'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('America/Fort_Nelson', 'America/Fort_Nelson'), ('EST5EDT', 'EST5EDT'), ('America/Cuiaba', 'America/Cuiaba'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('America/Yellowknife', 'America/Yellowknife'), ('Asia/Khandyga', 'Asia/Khandyga'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('Etc/GMT-9', 'Etc/GMT-9'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('America/Moncton', 'America/Moncton'), ('America/Merida', 'America/Merida'), ('America/Kralendijk', 'America/Kralendijk'), ('Atlantic/Faeroe', 'Atlantic/Faeroe'), ('Europe/Berlin', 'Europe/Berlin'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('Iran', 'Iran'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('Asia/Famagusta', 'Asia/Famagusta'), ('Asia/Chita', 'Asia/Chita'), ('EST', 'EST'), ('America/Guyana', 'America/Guyana'), ('America/Edmonton', 'America/Edmonton'), ('America/Guadeloupe', 'America/Guadeloupe'), ('Pacific/Majuro', 'Pacific/Majuro'), ('Pacific/Efate', 'Pacific/Efate'), ('America/Regina', 'America/Regina'), ('Europe/Simferopol', 'Europe/Simferopol'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('Africa/Ceuta', 'Africa/Ceuta'), ('Etc/GMT-12', 'Etc/GMT-12'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('Europe/Busingen', 'Europe/Busingen'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('GMT0', 'GMT0'), ('Europe/Oslo', 'Europe/Oslo'), ('Africa/Niamey', 'Africa/Niamey'), ('Europe/Samara', 'Europe/Samara'), ('Indian/Cocos', 'Indian/Cocos'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('Asia/Istanbul', 'Asia/Istanbul'), ('Asia/Beirut', 'Asia/Beirut'), ('Australia/LHI', 'Australia/LHI'), ('Canada/Central', 'Canada/Central'), ('PST8PDT', 'PST8PDT'), ('America/Panama', 'America/Panama'), ('UTC', 'UTC'), ('Australia/Perth', 'Australia/Perth'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('America/St_Lucia', 'America/St_Lucia'), ('America/St_Vincent', 'America/St_Vincent'), ('Europe/Vaduz', 'Europe/Vaduz'), ('America/Indianapolis', 'America/Indianapolis'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('Canada/Eastern', 'Canada/Eastern'), ('Africa/Lome', 'Africa/Lome'), ('Kwajalein', 'Kwajalein'), ('Europe/Bucharest', 'Europe/Bucharest'), ('Etc/GMT-10', 'Etc/GMT-10'), ('America/Anchorage', 'America/Anchorage'), ('Etc/GMT-2', 'Etc/GMT-2'), ('Israel', 'Israel'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('Europe/Skopje', 'Europe/Skopje'), ('Jamaica', 'Jamaica'), ('America/Montevideo', 'America/Montevideo'), ('Asia/Singapore', 'Asia/Singapore'), ('Africa/Bujumbura', 'Africa/Bujumbura')], default='UTC', max_length=50)),
                ('work_hours_start', models.TimeField()),
                ('work_hours_end', models.TimeField()),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
