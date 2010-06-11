class BaseRole:
    pr = False
    name = ''
    side = ''
    filesays = ''
    revealedtomafia = None
    seesmafia = False
    seesdead = False
    nightactions = []
    randomnightactions = []
    dayactions = []
    randomdayactions = []
    oneactions = []
    randomoneactions = []
    description = ''
    nightassignment = ''
    nightspeach = ''
    
    def __init__(self):
        self.hasactioned = False
        self.target = None
    
    def returnName(self): return self.name
        
    def returnSide(self): return self.side
        
    def returnFileSays(self): return self.filesays
    
    def changeFileSays(self):
        if self.filesays == 'mafia': self.filesays = 'town'
        elif self.filesays == 'town': self.filesays = 'mafia'
    
    def returnRevealedToMafia(self): return self.revealedtomafia
    
    def returnSeesMafia(self): return self.seesmafia
    
    def returnSeesDead(self): return self.seesdead
    
    def returnNightActions(self): return self.nightactions
    
    def returnRandomNightActions(self): return self.randomnightactions
    
    def returnDayActions(self): return self.dayactions
    
    def returnRandomDayActions(self): return self.randomdayactions
    
    def returnOneActions(self): return self.oneactions
    
    def returnRandomOneActions(self): return self.randomoneactions
    
    def returnDescription(self): return self.description
    
    def returnNightAssignment(self): return self.nightassignment
    
    def returnNightSpeach(self): return self.nightspeach
    
    def returnHasActioned(self): return self.hasvoted
    
    def changeHasActioned(self, FT): self.hasactioned = FT
    
    def returnTarget(self): return self.target
    
    def changeTarget(self, newtarget): self.target = newtarget
    
    def returnPR(self): return self.pr

class Mafioso(BaseRole):
    pr = True
    name = "Mafioso"
    side = "mafia"
    filesays = "mafia"
    revealedtomafia = True
    seesmafia = True
    seesdead = False
    nightactions = ['kill','mchat']
    dayactions = ['lynch','whisper']
    description = "[Mafia] The Mafioso is the standard mafia hitman. Power(s): kill (night)"
    nightassignment = "You are a run-of-the-mill Mafioso. As the Mafia's hitman, you have been tasked with killing off the townies while they sleep in their beds! Don't reveal yourself to the citizens or you will be lynched!"
    nightspeach = "As the citizens sleep, this is your time to strike as the Mafia's hitman! Decide whom you want to kill tonight, and PM me with 'kill <target>'."
        
class Sheriff(BaseRole):
    pr = True
    name = "Sheriff"
    side = "town"
    filesays = "town"
    revealedtomafia = False
    seesmafia = False
    seesdead = False
    nightactions = ['check']
    dayactions = ['lynch','whisper']
    description = "[Town] The Sheriff is the stereotypical cop; eating donuts while watching tv, the sheriff only has time to check one file a night. Power(s): check (night)"
    nightassignment = "You are the Sheriff. With your indepth files on each member of the town, you can check the file of one citizen a night. Don't reveal yourself to mafia, or you may be killed!"
    nightspeach = "After a long day's work and everyone is safely asleep, you have just enough time to look up the information on one citizen. To do so, PM me with 'check <citizen>'."
    
class OrdinaryCitizen(BaseRole):
    pr = False
    name = "Ordinary Citizen"
    side = "town"
    filesays = "town"
    revealedtomafia = False
    seesmafia = False
    seesdead = False
    nightactions = []
    dayactions = ['lynch','whisper']
    description = "[Town] A normal citizen without any special powers."
    nightassignment = "You are a simple citizen. Perhaps you are a student, or maybe even a tv repair man, either way you aren't really worth that much. So go to sleep, but keep an eye open for those pesky mafia!"
    nightspeach = "After a long day's work, or studying, or whatever you do, you can't wait to go to sleeepppp... zzzzzzz...."

        
class Doctor(BaseRole):
    pr = True
    name = "Doctor"
    side = "town"
    filesays = "town"
    revealedtomafia = False
    seesmafia = False
    seesdead = False
    nightactions = []
    dayactions = ['lynch','whisper']
    description = "[Town] A doctor can choose to save one other player each night from most attacks. Power(s): save (night)"
    nightassignment = "You are the Doctor. A townie skilled in the arts of healing, you have the ability to save one person a night from pretty much anything. Just make sure you lay low, if the mafia discover you... well, it was nice while it lasted."
    nightspeach = "Night falls and you don the cape of the skilled DOCTOR!. You're on a very strict schedule, Glee is on soon, so quickly choose one citizen to try to save. Make your decision and PM me 'save <citizen>'."

