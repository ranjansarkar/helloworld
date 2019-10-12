####################################################################################################
#	SCRIPTNAME		:ETRPROCESSSHIPMENT.py
#	SCRIPTTYPE		:ACTION (called by escalation)
#	AUTHOR			:Ranjan Sarkar <ranjan.sarkar@us.ibm.com>
#	Description 	:Script iterates through the set of assets and perform bulk operations like change
#					status, field updates, location moves.
#					The script uses GVL(PLUSDCVAL) to get the execution parameters and comm templates 
#					to notify support group in case of errors.
#	InputParameters	:
#	Name 			:	escalationName
#	Variable type	:	IN
#	Binding type	:	LITERAL
#	Description 	:	Name of the escalation the script is tied to
#
#	Name 			:	logSuccess
#	Variable type	:	IN
#	Binding type	:	LITERAL
#	Description 	:	Create a log entry Shipment record for each successful asset update
#
#	Name 			:	sendEmailtoOpsCommTemplate
#	Variable type	:	IN
#	Binding type	:	SYSPROP
#	Description 	:	Comm Template to send email to OPS team, gets value 
#						from system property etr.autoscript.opsemailcommtemplate
#
#
#	Modification History:
#	Date			User				Comment
#===================================================================================================
#	Dec 26, 2017	Ranjan Sarkar		Initial version
#	Dec 27, 2017	Ranjan Sarkar		Updated version

#	Jan 29, 2017	Ranjan Sarkar		Jan 29 changes version - merged
#	Oct 12, 2019	Ranjan Sarkar		Testing Git Commit from SourceTree from vscode 3
#	Oct 12, 2019	Ranjan Sarkar		Added new line from vscode 5
####################################################################################################


from psdi.mbo import MboConstants
from psdi.util.logging import MXLoggerFactory
from java.util import Date
from psdi.txn import MXTransaction
from psdi.mbo import MboSetRemote
from psdi.server import MXServer
from java.text import DateFormat
from java.text import SimpleDateFormat

##############Global definition : Start ##########
SCRIPTLOGGER = MXLoggerFactory.getLogger("maximo.entergy.autoscript.etrprocessshipment");
ticketID = mbo.getString("TICKETID")
srStatus=mbo.getString("STATUS")
ticketUID=mbo.getString("TICKETUID")
srMoveToLoc=mbo.getString("ETRMOVE2LOC")
srMoveToStatus=mbo.getString("ETRMOVE2STAT")
srRMANum=mbo.getString("ETRRMANUM")
gvlSendCommTemplateEmail="NO"
gvlCommTemplate="BLANK"
isError = False

##############Global definition : Start ##########

#FUNCTION SCRIPT_PRINT : Start
# Arguments	 
# Name 			: logMesage
# DESCRIPTION 	: message to be logged
#
def SCRIPT_PRINT(logMesage):
	#print processname + " : " + logMesage
	SCRIPTLOGGER.info(scriptName + " : " + str(logMesage))
#FUNCTION SCRIPT_PRINT : End

#FUNCTION postProcessSR
# Arguments	 
# Name 			: srStatusMsgLocal
# DESCRIPTION 	: The message to be used when changing the status to ERROR
#
# Name 			: isErrorLocal
# DESCRIPTION 	: boolean variable to indicate error condition
#
# : Start
def postProcessSR(srStatusMsgLocal,isErrorLocal):
	SCRIPT_PRINT("start function  postProcessSR()")
	SCRIPT_PRINT("isErrorLocal : " + str(isErrorLocal))
	SCRIPT_PRINT("srStatusMsgLocal : " + str(srStatusMsgLocal))
	#get the SR again as once the save is called any update made to SR after that was gettig discarded
	srSet = MXServer.getMXServer().getMboSet("SR", mbo.getUserInfo());
	srSet.setWhere("TICKETUID = "+str(ticketUID));
	srSet.reset();
	sr = srSet.getMbo(0)
	SCRIPT_PRINT("Processing change status on SR : ticketID : " + str(ticketID) + " ticketUID : " + str(ticketUID))
	if(isErrorLocal):
		sr.changeStatus(srStatus+"_E",Date(),srStatusMsgLocal[0:48])
		sr.setValue("ETRSHIPERR",srStatusMsgLocal)
	else:
		sr.changeStatus(srStatus+"_C",Date(),"Staus changed by Shipment application processing")
		sr.setValue("ETRMOVE2LOC",None)
		sr.setValue("ETRMOVE2STAT",None)
		sr.setValue("ETRRMANUM",None)
		sr.setValue("ETRSHIPERR",None)
	sr.setValue("ETRISPROCESS",0)
	SCRIPT_PRINT("SR update complete")
	srSet.save()

	if(sendEmailtoOpsCommTemplate == None):
		srSet.close()
		raise MXApplicationException("etrshipment","syspropnotset")
	#End of if
	if(isErrorLocal):
		#Get the escalation to associate it with the comm template log
		escSet = MXServer.getMXServer().getMboSet("ESCALATION", mbo.getUserInfo());
		escSet.setWhere("ESCALATION = '"+ escalationName.upper() + "'");
		SCRIPT_PRINT("Escalation where clause: " + str(escSet.getCompleteWhere()))
		escSet.setFlag(MboConstants.DISCARDABLE, True);
		escSet.reset();
		esc = escSet.getMbo(0)
		#Get the comm template
		csr = MXServer.getMXServer().getMboSet("COMMTEMPLATE", MXServer.getMXServer().getSystemUserInfo());
		csr.setWhere("templateid='"+ sendEmailtoOpsCommTemplate + "'");
		SCRIPT_PRINT("Comm template where clause: " + str(csr.getCompleteWhere()))
		csr.reset();
		ctr = csr.getMbo(0);
		ctr.sendMessage(sr, esc);
		SCRIPT_PRINT("Comm template executed")
		escSet.close()
		srSet.close()
	SCRIPT_PRINT("end function  postProcessSR()")
#FUNCTION postProcessSR : End


SCRIPT_PRINT("start script ************************************ v1.0")
SCRIPT_PRINT("Shipment Record : " + ticketID)


##############Core logic starts####################

#get the GVL record for the operation
gvlSet = mbo.getMboSet("ETRPLUSDCVAL")
SCRIPT_PRINT(gvlSet.getCompleteWhere())
gvl = gvlSet.getMbo(0)

if (gvl is None):
	srStatusMsg= "Error in processing : NOGVLFOUND"
	postProcessSR(srStatusMsg,True)
else:
	try:
		#Had to get the SR from MXServer as logic to reuse the SR from escalation didn't worked. Any change to SR after first mboSet.save() was
		#getting discarded by framework. 
		srSet = MXServer.getMXServer().getMboSet("SR", mbo.getUserInfo());
		srSet.setWhere("TICKETUID = "+str(ticketUID));
		srSet.reset();
		sr = srSet.getMbo(0)
		sr.setValue("ETRISPROCESS",1)
		#SCRIPT_PRINT("IS MBOSet to be toBeSaved before save: " + str(mbo.getThisMboSet().toBeSaved()))
		srSet.save()
		srSet.close()
		srStatusMsg= "Error in processing : PostSR ETRISPROCESS"

		#get the SR again as we are going to do bulk processing. Also if I use the same MboSet any update (change status or field update) made to SR after the save is called was gettig discarded
		srSet = MXServer.getMXServer().getMboSet("SR", mbo.getUserInfo());
		srSet.setWhere("TICKETUID = "+str(ticketUID));
		srSet.reset();
		sr = srSet.getMbo(0)
		srLogSet = sr.getMboSet("ETRSHIPLOG")
		
		#set the variables from gvl : Start
		gvlCommTemplate=gvl.getString("VALUE01")
		gvlSendCommTemplateEmail=gvl.getString("VALUE02")
		SCRIPT_PRINT("srMoveToStatus : " + str(srMoveToStatus))
		SCRIPT_PRINT("srMoveToLoc : " + str(srMoveToLoc))
		SCRIPT_PRINT("gvlCommTemplate : " + str(gvlCommTemplate))
		SCRIPT_PRINT("gvlSendCommTemplateEmail : " + str(gvlSendCommTemplateEmail))
		#set the variables from gvl : End
		srStatusMsg= "Error in processing : PostGVL"

		#get all the assets in the shipment
		assetSet = sr.getMboSet("ETRSHIPMENTNUM")
		SCRIPT_PRINT(assetSet.getCompleteWhere())
		assetRecords = 0
		asset = assetSet.getMbo(assetRecords)
		batchID = ticketID + SimpleDateFormat("yyyyMMddHHmmssSSS").format(Date())
		while (asset is not None):
			try:
				assetnum = asset.getString("assetnum")
				assetStatus = asset.getString("status")
				assetSite = asset.getString("SITEID")
				assetOrg = asset.getString("ORGID")
				assetMsgSts=""
				assetMsg=""
				SCRIPT_PRINT("Processing assetnum : " + assetnum + " Record number : " + str(assetRecords))
				#process change status : Start
				if(srStatus=="MV2STLOC" or srStatus=="MV2STAT"):
					if(assetStatus != srMoveToStatus):
						SCRIPT_PRINT("Going to perform asset change status..")
						asset.changeStatus(srMoveToStatus,Date(),"Staus changed by Shipment application processing")
						assetMsg = "Asset status changed from : "+ assetStatus + " to new status : "+ srMoveToStatus
						assetMsgSts = "STATUS_CHANGED"
					else:
						assetMsg = "Asset change status skipped as the new status : "+ srMoveToStatus +" is same as current status :"+ assetStatus
						assetMsgSts = "STATUS_CHANGE_SKIPPED"
					#End of if
				#End of if
				#process change status : End

				#process change location : Start
				if(srStatus=="MV2STLOC" or srStatus=="MV2STLOC"):
					assetLoc = asset.getString("LOCATION")
					if(assetLoc != srMoveToLoc):
						asset.setValue("NEWSITE",assetSite);
						asset.setValue("NEWLOCATION",srMoveToLoc);
						asset.setValue("NEWPARENT",asset.getString("PARENT"));
						SCRIPT_PRINT("Going to perform asset move..")
						assetSet.moveSingleAsset(asset);
						assetMsg = "Asset moved from : " + assetLoc + " to : " + srMoveToLoc
						assetMsgSts = "LOCATION_CHANGED"
					else:
						if(assetMsgSts == "STATUS_CHANGE_SKIPPED"):
							assetMsg = assetMsg + " and Asset moved skipped as the new location : "+ srMoveToLoc +" is same as current location :"+ assetLoc
							assetMsgSts = "STS_LOC_CHANGE_SKIPPED"
						else:
							assetMsg = "Asset moved skipped as the new location : "+ srMoveToLoc +" is same as current location :"+ assetLoc
							assetMsgSts = "LOCATION_CHANGE_SKIPPED"
				#End of if
				#process change location : End

				#process RMA batch number : Start
				elif(srStatus=="MV2RMA"):
					asset.setValue("ETRRMANUM",srRMANum);
					assetMsg = "Asset RMA Batch updated to : " + srRMANum
					assetMsgSts = "RMA_CHANGED"
				#End of if
				#process RMA batch number : End

				#process isFATMeter : Start
				elif(srStatus=="MARKFAT"):
					asset.setValue("ETRISFAT",True);
					assetMsg = "Asset isFAT flag set to TRUE"
					assetMsgSts = "ISFAT_CHANGED"
				#End of if
				#process isFATMeter : End
				SCRIPT_PRINT(assetMsg)
				SCRIPT_PRINT("Processed assetnum : " + assetnum + " without error")
			#End of try
			except Exception, myErr:
				SCRIPT_PRINT("Got Error")
				# Log error entry : Start
				srLog = srLogSet.add()
				srLog.setValue("BATCHID",batchID)
				srLog.setValue("TICKETID",ticketID)
				srLog.setValue("ASSETNUM",assetnum)
				srLog.setValue("DESCRIPTION",str(myErr)[0:900])
				srLog.setValue("STATUS","ERROR")
				srLog.setValue("ORGID",assetOrg)
				srLog.setValue("SITEID",assetSite)
				isError = True
				srStatusMsg= "Error in processing : AssetProcess : assetnum : " + assetnum + " with error : " + str(myErr)[0:900]
				# Log error entry : End
				SCRIPT_PRINT(srStatusMsg)
			#End of except
			else:# else of try 
				SCRIPT_PRINT("In Success Condition")
				if(logSuccess.upper()=="YES"):
					SCRIPT_PRINT("Going to log Success")
					# Log successful entry : Start
					srLog = srLogSet.add()
					srLog.setValue("BATCHID",batchID)
					srLog.setValue("TICKETID",ticketID)
					srLog.setValue("ASSETNUM",assetnum)
					srLog.setValue("DESCRIPTION",assetMsg)
					srLog.setValue("STATUS",assetMsgSts)
					srLog.setValue("ORGID",assetOrg)
					srLog.setValue("SITEID",assetSite)
					# Log successful entry : End
					SCRIPT_PRINT("Added log entry of the success in ETRSHIPLOG for assetnum : " + assetnum )
			#End of try else

			srSet.save()
			assetRecords = assetRecords + 1
			asset = assetSet.getMbo(assetRecords)
			SCRIPT_PRINT("Last statement of While loop")
		#End of while loop
		srSet.close()

		postProcessSR(srStatusMsg,isError)
		SCRIPT_PRINT("After processing status change on SR : " + mbo.getString("STATUS"))
		srStatusMsg = "Error in processing : PostSR ASSET Processing"
		#Send an email about the action
		SCRIPT_PRINT("isError : "+ str(isError) + " gvlSendCommTemplateEmail : " + str(gvlSendCommTemplateEmail) + " gvlCommTemplate : " + str(gvlCommTemplate))
		if(isError == False and gvlSendCommTemplateEmail.upper() == "YES" and gvlCommTemplate != "BLANK"):
			csr = MXServer.getMXServer().getMboSet("COMMTEMPLATE", MXServer.getMXServer().getSystemUserInfo());
			csr.setWhere("templateid='"+ gvlCommTemplate.upper() + "'");
			SCRIPT_PRINT("Comm template to users with where clause: " + str(csr.getCompleteWhere()))
			csr.reset();
			ctr = csr.getMbo(0);
			ctr.sendMessage(mbo, None)
			SCRIPT_PRINT("Comm template executed")
		else:
			SCRIPT_PRINT("Not executing Comm template for this mass action. Either there was an error or no Comm Template specified in PLUSDCVAL or Comm Template flag is disabled in PLUSDCVAL")
		#End of if
	except Exception, myErr:
		SCRIPT_PRINT("Error in processing Shipment Record :"+ ticketID + " with status : "+ srStatus + " ERROR : " + str(myErr))
		postProcessSR((srStatusMsg + " ERROR : " + str(myErr))[0:900],True)
	#End of SR processing try
#End of main else
SCRIPT_PRINT("end script ************************************")
#################Script End#####################
