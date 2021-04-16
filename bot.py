import discord, asyncio, json, random, datetime, re

f = open('setupinfo.json', encoding='utf8')
setup_inf = json.load(f)
f.close()

dscl = discord.Client()

def log(strrr):
    now = datetime.datetime.now()
    print("[%s-%02d-%02d %02d:%02d:%02d] :: %s" % (now.year, now.month, now.day, now.hour, now.minute, now.second, strrr))

def isAllowChannel(channelid, guildid):
    if int(setup_inf['Guilds'][str(guildid)]['allowIssueChannel']) == channelid:
        log("[Matching Issue Channel ID]\nInputID : %s\nDataID : %s\n" % (channelid, setup_inf['Guilds'][str(guildid)]['allowIssueChannel']))
        return True
    else:
        print("[Mismatch with Issue Channel ID]\nInputID : %s\n" % (channelid))
        return False

def isBlockedUsr(userid):
    for now_usrID in setup_inf['blockedUser']:
        if int(now_usrID) == userid:
            log("[Matching Blocked Usr ID]\nInputID : %s\nDataID : %s\n" % (userid, now_usrID))
            return True
        else:
            continue
    # log("[Mismatch with Blocked Usr ID]\nInputID : %s\n" % (userid))
    return False

def isAddedAdmin(userid, guildid):
    for now_usrID in setup_inf['Guilds'][str(guildid)]['Managers']:
        if int(now_usrID) == userid:
            log("[Matching administrator ID]\nInputID : %s\nDataID : %s\n" % (userid, now_usrID))
            return True
        else:
            continue
    log("[Mismatch with Administrator ID]\nInputID : %s\n" % (userid))
    return False

@dscl.event
async def on_ready():
    await dscl.change_presence(status=discord.Status.online, activity=discord.Game("!발행 <내용>으로 티켓을 발급 해 보세요."))
    log("%s is Ready!" % (dscl.user.name))
  
@dscl.event
async def on_message(message):
    if message.author.bot or (str(type(message.channel)) == "<class 'discord.channel.DMChannel'>"):
        return None

    if isBlockedUsr(message.author.id):
        return None

    def pred(m): # await app.wait_for('message', check=pred)
        return m.author == message.author# and m.channel == message.channel

    if message.content == "!T":
        orderNum = 1
        departLists = ''
        for now_departID in setup_inf['Guilds'][str(message.guild.id)]['Categories']:
            departLists = departLists + '%s. <@&%s> : `%s`\n' % (orderNum, now_departID, setup_inf['Guilds'][str(message.guild.id)]['Categories'][str(now_departID)])
            orderNum += 1
        print(departLists)

    now = datetime.datetime.now()

    if message.content.startswith('!발행 '):
        if isAllowChannel(message.channel.id, message.guild.id):
            # 티켓 넘버 : YYYYMMDD-qwer
            await message.delete()
            ticketNumber = "%s%02d%02d-%s" % (now.year, now.month, now.day, random.randint(1000, 9999))
            topic = message.content.replace('!발행 ', '')
            def question_check(reaction, user):
                return (str(reaction.emoji) == '🌐' or str(reaction.emoji) == '🔒') and user == message.author
            ticketChannel = await message.guild.create_text_channel(name="티켓-%s" % (ticketNumber), category=message.channel.category, nsfw=False, topic="[T] %s (%s#%s)님이 발급한 티켓입니다. | Status : Open" % (message.author.id, message.author.name, message.author.discriminator))
            await message.channel.send("<@%s>, <#%s> 채널에서 티켓 발행을 마무리 해 주세요." % (message.author.id, ticketChannel.id))

            # 채널 기본 셋업
            await ticketChannel.edit(sync_permissions=False)
            await ticketChannel.set_permissions(message.guild.default_role, read_messages=False, add_reactions=False)
            await ticketChannel.set_permissions(message.author, read_messages=True, add_reactions=False)

            # 공개여부
            embed = discord.Embed(title="%s 티켓이 발행되었습니다." % (ticketNumber), description="🌐 : 전체공개\n🔒 : 본인만 보기\n\n하단 반응을 눌러 티켓의 공개여부를 입력 해 주세요.\n120초 안에 입력하지 않으실 경우, 해당 티켓은 자동으로 닫히게 됩니다.", color=0x62c1cc)
            embed.set_footer(text="© 2018-2020 Develable")
            privacy_check_message = await ticketChannel.send(embed=embed)
            await privacy_check_message.add_reaction('🌐')
            await privacy_check_message.add_reaction('🔒')
            try:
                reaction, user = await dscl.wait_for('reaction_add', timeout=120.0, check=question_check)
            except asyncio.TimeoutError:
                await ticketChannel.send("<@%s>, 120초 경과로 인하여 해당 티켓은 닫힘 처리됩니다." % (message.author.id))
                await ticketChannel.set_permissions(message.guild.default_role, read_messages=True, send_messages=False)
                await ticketChannel.set_permissions(message.author, overwrite=None)
                await ticketChannel.edit(category=message.guild.get_channel(int(setup_inf['Guilds'][str(message.guild.id)]['closedTicketCategory'])), topic=ticketChannel.topic.replace(" | Status : Open", " | Status : Closed (Timeout)"))
            else:
                if reaction.emoji == "🌐":
                    await ticketChannel.send("티켓의 공개 여부가 `전체공개`로 선택되었습니다.")
                    await ticketChannel.set_permissions(message.guild.default_role, read_messages=True, send_messages=False)
                    await ticketChannel.set_permissions(message.author, read_messages=True, add_reactions=False, send_messages=True)
                else:
                    await ticketChannel.set_permissions(message.author, read_messages=True, add_reactions=False, send_messages=True)
                    await ticketChannel.send("티켓의 공개 여부가 `본인만 보기`로 선택되었습니다.")

                # 2020-06-21 추가 : 부서선택
                orderNum = 1
                departLists = '부서 선택하실 때 좌측에 있는 번호를 입력하세요\n\n'
                for now_departID in setup_inf['Guilds'][str(message.guild.id)]['Categories']:
                    departLists = departLists + '%s. <@&%s> : %s\n' % (orderNum, now_departID, setup_inf['Guilds'][str(message.guild.id)]['Categories'][str(now_departID)])
                    orderNum += 1

                embed = discord.Embed(title="답변 부서를 선택하세요.", description=departLists, color=0x62c1cc)
                embed.set_footer(text="© 2018-2020 Develable")
                await ticketChannel.send(embed=embed)
                departRes = await dscl.wait_for('message', check=pred)
                await departRes.delete()
                target = re.findall(r'\d+', departRes.content)
                target = target[0]
                target = int(target)

                orderNum = 1
                for now_departID in setup_inf['Guilds'][str(message.guild.id)]['Categories']:
                    if orderNum == target:
                        callDepartID = now_departID
                        break
                    orderNum += 1

                await ticketChannel.set_permissions(message.guild.get_role(int(callDepartID)), read_messages=True, add_reactions=False, manage_messages=True, send_messages=True)
                await ticketChannel.edit(topic=ticketChannel.topic + " | CallDep : %s" % (callDepartID))

                # 발급 완료
                notice = await ticketChannel.send("티켓이 정상적으로 발급되었습니다.\n봇 관리자와 티켓 발급자는 언제든지 `!완료`를 입력하여 티켓을 닫을 수 있으며, 한번 닫은 티켓은 다시 열 수 없습니다.\n\n```%s```\n<@&%s>" % (topic, callDepartID))
                await notice.pin()
        else:
            await message.channel.send("<@%s>, 티켓 발급을 진행 할 수 없는 채널입니다." % (message.author.id))

    if message.content == "!완료":
        if isAllowChannel(message.channel.id, message.guild.id):
            await message.channel.send("<@%s>, 해당 채널은 닫을 수 없습니다." % (message.author.id))
        else:
            if message.channel.topic.startswith('[T] '):
                ticketChannel_inf = message.channel.topic
                issuerid = ticketChannel_inf.replace('[T] ', '')
                issuerid = issuerid.split("(")[0]
                issuerid = re.findall(r'\d+', issuerid)
                issuerid = issuerid[0]
                issuerid = int(issuerid)
                managerid = ticketChannel_inf.split(' | CallDep : ')
                managerid = str(managerid[len(managerid) - 1])
                managerid = re.findall(r'\d+', managerid)
                managerid = managerid[0]
                managerid = int(managerid)
                if message.author.id == int(issuerid) or isAddedAdmin(message.author.id, message.guild.id):
                    await message.channel.set_permissions(message.guild.get_role(int(managerid)), read_messages=True, add_reactions=False, manage_messages=False, send_messages=False)
                    await message.channel.set_permissions(message.guild.get_member(int(issuerid)), read_messages=True, add_reactions=False, send_messages=False)
                    await message.channel.edit(category=message.guild.get_channel(int(setup_inf['Guilds'][str(message.guild.id)]['closedTicketCategory'])), topic=message.channel.topic.replace(" | Status : Open", " | Status : Closed (%s)" % ("Manager" if isAddedAdmin(message.author.id, message.guild.id) else "Issuer")))
                    await message.channel.send("<@%s>, 티켓이 닫힘 처리 되었습니다." % (message.author.id))
                else:
                    await message.channel.send("<@%s>, 티켓 발급자와 등록된 관리자만 해당 티켓을 닫을 수 있습니다." % (message.author.id))
            else:
                await message.channel.send("<@%s>, 해당 채널은 닫을 수 없습니다." % (message.author.id))

dscl.run(setup_inf['token'])