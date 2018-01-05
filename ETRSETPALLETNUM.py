####################################################################################################
#	SCRIPTNAME		:ETRSETPALLETNUM.py
#	SCRIPTTYPE		:ATTRIBUTE LAUNCTPOINT on ASSET.ETRSHIPNUM
#	AUTHOR			:Ranjan Sarkar <ranjan.sarkar@us.ibm.com>
#	Description 	:Script propogates the value custom attrobute ETRSHIPNUM to ETRPALLETNUM
#	InputParameters	:
#	Name 			:	etrPalletNum
#	Variable type	:	INOUT
#	Binding type	:	ATTRIBUTE
#	Description 	:	ASSET.ETRPALLETNUM
#
#	Name 			:	etrShipNum
#	Variable type	:	IN
#	Binding type	:	ATTRIBUTE
#	Description 	:	ASSET.ETRSHIPNUM
#
#	Modification History:
#	Date			User				Comment
#===================================================================================================
#	Dec 26, 2017	Ranjan Sarkar		Initial version
####################################################################################################

#################Script Start###################
if(etrPalletNum is None or etrPalletNum == ""):
	etrPalletNum = etrShipNum
#################Script End#####################