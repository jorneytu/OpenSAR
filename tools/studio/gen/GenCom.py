import sys,os
import xml.etree.ElementTree as ET
from GenCanIf import GenCanIf
from GenCanTp import GenCanTp
from GenPduR import GenPduR

__all__ = ['GenCom']


__Header = \
"""/*
* Configuration of module: Com
*
* Created by:   parai          
* Copyright:    (C)parai@foxmail.com  
*
* Configured for (MCU):    MinGW ...
*
* Module vendor:           ArcCore
* Generator version:       2.0.34
*
* Generated by easySAR Studio (https://github.com/parai/OpenSAR)
*/
"""

__dir = '.'
__root = None

def GenCom(wfxml):
    global __dir,__root
    __root = ET.parse(wfxml).getroot();
    __dir = os.path.dirname(wfxml)
    GenCanIf(wfxml)
    GenCanTp(wfxml)
    GenPduR (wfxml)
    GenH()
    GenC()
    GenPy()


def tInt(strnum):
    if(strnum.find('0x')!=-1 or strnum.find('0X')!=-1):
        return int(strnum,16)
    else:
        return int(strnum,10)
    
def GAGet(what,which):
    # what must be a pdu = [ Name, Id, Bus]
    # or a Signal Node
    try:
        if(which == 'name'):
            return what[0]
        elif(which == 'id'):
            return hex(tInt(what[1]))
        elif(which == 'bus'):
            return what[2]
        else:
            raise Exception('No Found')
    except:
        import re
        # (Type=RX/TX ) (Name) (Id)
        reMsg = re.compile(r'(\w+)\s*=\s*(\w+)\s*\(\s*(\w+)\s*\)')
        msg = what.attrib['msg']
        msg = reMsg.search(msg).groups()
        if(which == 'msgname'):
            return msg[1]
        elif(which == 'msgtype'):
            return msg[0]
        elif(which == 'type'):
            size = tInt(what.attrib['size'])
            if(size <= 8):
                return 'UINT8'
            elif(size <= 16):
                return 'UINT16'
            elif(size <= 32):
                 return 'UINT32'
            else:
                return 'UINT8_N'
        else:
            return what.attrib[which]

def GLGet(what,which = None):
    """ Gen Get List
        Get A Special List []
    """
    global __root
    import re
    # (Type=RX/TX ) (Name) (Id)
    reMsg = re.compile(r'(\w+)\s*=\s*(\w+)\s*\(\s*(\w+)\s*\)')
    if(which!=None and which=='SignalRefs'):
        # what is a pdu = [ Name, Id, Bus]
        rList = []
        for sig in __root.find('SignalList'):
            import re
            # (Type=RX/TX ) (Name) (Id)
            reMsg = re.compile(r'(\w+)\s*=\s*(\w+)\s*\(\s*(\w+)\s*\)')
            msg = sig.attrib['msg']
            msg = reMsg.search(msg).groups()
            if(what[0]==msg[1] and what[1]==msg[2] and what[2]==sig.attrib['bus']):
                rList.append(sig)
        return rList
    if(what == 'Signal'):
        return __root.find('SignalList')
    rlist =[]
    if(what == 'TxPdu'):
        for Signal in __root.find('SignalList'):
            msg = Signal.attrib['msg']
            try:
                msg = reMsg.search(msg).groups()
                if(msg[0] == 'TX'):
                   flag = False
                   for pdu in rlist:
                       # If has same Id and Bus
                       if(msg[2] == pdu[1] and Signal.attrib['bus'] == pdu[2]):
                           if(msg[1]) != pdu[0]:
                               raise Exception('Name must be the same if the message has the same Id on the same Bus.')
                           flag = True
                   if(False == flag):
                       pdu = []
                       pdu.append(msg[1])
                       pdu.append(msg[2])
                       pdu.append(Signal.attrib['bus'])
                       rlist.append(pdu)
            except:
                print traceback.format_exc()
                print 'PduR: Error Message Configured for %s'%(Signal.attrib['name'])
    elif(what == 'RxPdu'):
        for Signal in __root.find('SignalList'):
            msg = Signal.attrib['msg']
            try:
                msg = reMsg.search(msg).groups()
                if(msg[0] == 'RX'):
                   flag = False
                   for pdu in rlist:
                       if(msg[2] == pdu[1] and Signal.attrib['bus'] == pdu[2]):
                           if(msg[1]) != pdu[0]:
                               raise Exception('Name must be the same if the message has the same Id on the same Bus.')
                           flag = True
                   if(False == flag):
                       pdu = []
                       pdu.append(msg[1])
                       pdu.append(msg[2])
                       pdu.append(Signal.attrib['bus'])
                       rlist.append(pdu)
            except:
                print traceback.format_exc()
                print 'PduR: Error Message Configured for %s'%(Signal.attrib['name'])
    return rlist

def GenH():
    global __dir
    # =========================  PduR_Cfg.h ==================
    fp = open('%s/Com_Cfg.h'%(__dir),'w')
    fp.write(__Header)
    fp.write("""

#if !(((COM_SW_MAJOR_VERSION == 1) && (COM_SW_MINOR_VERSION == 2)))
#error Com: Configuration file expected BSW module version to be 1.2.*
#endif

#ifndef COM_CFG_H_
#define COM_CFG_H_

#define COM_MODULE_ID 20
#define COM_INSTANCE_ID 1
#define COM_E_INVALID_FILTER_CONFIGURATION 101
#define COM_E_INITIALIZATION_FAILED 102
#define COM_E_INVALID_SIGNAL_CONFIGURATION 103
#define COM_INVALID_PDU_ID 104
#define COM_INVALID_SIGNAL_ID 109
#define COM_ERROR_SIGNAL_IS_SIGNALGROUP 105
#define COM_E_TOO_MANY_IPDU 106
#define COM_E_TOO_MANY_SIGNAL 107
#define COM_E_TOO_MANY_GROUPSIGNAL 108
#define CPU_ENDIANESS cfgCPU_ENDIAN

#define COM_DEV_ERROR_DETECT STD_OFF

#define COM_N_IPDUS %s
#define COM_N_SIGNALS %s
#define COM_N_GROUP_SIGNALS 0 // TODO: not support by easyCom studio

#define ComConfigurationTimeBase 0
#define ComVersionInfoApi

#endif /*COM_CFG_H*/
    """%(len(GLGet('RxPdu')+GLGet('TxPdu')),len(GLGet('Signal')) ))
    fp.close()
    # ====================
    fp = open('%s/Com_PbCfg.h'%(__dir),'w')
    fp.write(__Header)
    fp.write("""
#if !(((COM_SW_MAJOR_VERSION == 1) && (COM_SW_MINOR_VERSION == 2)) )
#error Com: Configuration file expected BSW module version to be 1.2.*
#endif

#ifndef COM_PBCFG_H
#define COM_PBCFG_H

#include "Com_Types.h"

extern const Com_ConfigType ComConfiguration;

// PDU group id definitions    
#define COM_DEFAULT_IPDU_GROUP  0
    """)
    cstr = ''
    id = 0
    for pdu in GLGet('RxPdu'):
        cstr += '#define COM_%s_RX %s\n'%(GAGet(pdu,'name'),id)
        id += 1
    for pdu in GLGet('TxPdu'):
        cstr += '#define COM_%s_TX %s\n'%(GAGet(pdu,'name'),id)
        id += 1
    fp.write("""
//  COM IPDU Id Defines.
%s    
    """%(cstr))
    id = 0
    cstr = ''
    for sig in GLGet('Signal'):
        cstr += '#define COM_SID_%s %s\n'%(GAGet(sig,'name'),id)
        id += 1
    fp.write("""
//General Signal (Group) Id defines
%s

//Group Signal Id defines
// TODO: not supported by easyCom

// Notifications
// TODO: not supported by easyCom

// Callouts
// TODO: not supported by easyCom
#endif /* COM_PBCFG_H */    
    """%(cstr))
    fp.close()

def GenSigInitValue(Signal,fp):
    Size = tInt(GAGet(Signal,'size'))
    Init = tInt(GAGet(Signal,'init'))
    Length  = (Size+7)/8
    if(Size > 32):
        cstr = 'const uint8 %s_InitValue[%s] ={'%(GAGet(Signal,'name'),Length)
        for B in range(0,Length):
            cstr += '%s,'%( hex( (Init>>(8*( Length - B -1 )))&0xFF ))
        cstr += '}; // %s = %s\n'%(Init,hex(Init))
    else:
        if(Size <= 8):
            cstr = 'const uint8 %s_InitValue = %s;\n'%(GAGet(Signal,'name'),Init)
        elif(Size <= 16):
            cstr = 'const uint16 %s_InitValue = %s;\n'%(GAGet(Signal,'name'),Init)
        elif(Size <= 32):
            cstr = 'const uint32 %s_InitValue = %s;\n'%(GAGet(Signal,'name'),Init)
    fp.write(cstr)
def GenC():
    fp = open('%s/Com_PbCfg.c'%(__dir),'w')
    fp.write(__Header)
    fp.write("""
#include "Com.h"
#include "Com_Internal.h"
//#include <stdlib.h>
#if defined(USE_PDUR)
#include "PduR.h"
#endif 

//Signal init values.\n""")
    for sig in GLGet('Signal'):
        GenSigInitValue(sig,fp)
    fp.write("""
#if 0    
#if(COM_N_GROUP_SIGNALS > 0)
// This is an example as Not supported by easyCom
const ComGroupSignal_type ComGroupSignal[] = {
    {
        .ComBitPosition= 24,
        .ComBitSize= 8,
        .ComHandleId= COM PDUID,
        .ComSignalEndianess= cfgCPU_ENDIAN,
        .ComSignalInitValue= &name_InitValue,
        .ComSignalType= UINT8_N,
        .Com_Arc_EOL= FALSE
    },
    {
       .ComBitPosition= 32,
       .ComBitSize= 8,
       .ComHandleId= COM PDUID,
       .ComSignalEndianess= cfgCPU_ENDIAN,
       .ComSignalInitValue= &name_InitValue,
       .ComSignalType= UINT8_N,
       .Com_Arc_EOL= FALSE
    },
};
//SignalGroup GroupSignals lists.
const ComGroupSignal_type * const COM PDUID_SignalRefs[] = {
    &ComGroupSignal[ 0 ],
    &ComGroupSignal[ 1 ],
    NULL
};
#endif
#endif //0

//IPdu buffers and signal group buffers
""") 
    for pdu in GLGet('RxPdu'): 
        fp.write('uint8 %s_RX_IPduBuffer[8];\n'%(GAGet(pdu,'name'))) 
    for pdu in GLGet('TxPdu'): 
        fp.write('uint8 %s_TX_IPduBuffer[8];\n'%(GAGet(pdu,'name')))   
    cstr = ''
    id = 0
    for sig in GLGet('Signal'):
        cstr += """
    {
        .ComBitPosition =  %s,
        .ComBitSize =  %s,
        .ComErrorNotification =  NULL,
        .ComFirstTimeoutFactor =  10, // TODO: In Tick
        .ComHandleId =  COM_SID_%s,
        .ComNotification =  NULL,
        .ComRxDataTimeoutAction =  COM_TIMEOUT_DATA_ACTION_NONE,
        .ComSignalEndianess =  cfgCPU_ENDIAN, 
        .ComSignalInitValue =  &%s_InitValue,
        .ComSignalType =  %s,
        .ComTimeoutFactor =  10,
        .ComTimeoutNotification =  NULL,
        .ComTransferProperty =  PENDING,    // TODO: only useful when TX
        .ComUpdateBitPosition =  0,         // TODO
        .ComSignalArcUseUpdateBit =  FALSE, // TODO
        .Com_Arc_IsSignalGroup =  FALSE,
        .ComGroupSignal =  NULL,
        .Com_Arc_ShadowBuffer =  NULL,
        .Com_Arc_ShadowBuffer_Mask =  NULL,
        .ComIPduHandleId = COM_%s_%s,
        .Com_Arc_EOL =  FALSE
    },\n"""%(GAGet(sig,'start'),
             GAGet(sig,'size'),
             GAGet(sig,'name'),
             GAGet(sig,'name'),
             GAGet(sig, 'type'),
             GAGet(sig,'msgname'),
             GAGet(sig,'msgtype')
             )
    fp.write("""
//Signal definitions
const ComSignal_type ComSignal[] = {
%s
    {
         .Com_Arc_EOL =  True,
    }
};\n\n    """%(cstr))
    fp.write("""
//I-PDU group definitions
const ComIPduGroup_type ComIPduGroup[] = {
    {
        .ComIPduGroupHandleId =  COM_DEFAULT_IPDU_GROUP, // -> default
        .Com_Arc_EOL =  TRUE
    },
};    
    """)
    cstr = ''
    for pdu in GLGet('RxPdu'):
        cstr += 'const ComSignal_type * const %s_RX_SignalRefs[] = {\n'%(GAGet(pdu,'name'))
        for sig in GLGet(pdu,'SignalRefs'):
            cstr += '\t&ComSignal[ COM_SID_%s ],\n'%(GAGet(sig,'name'))
        cstr += '\tNULL\n};\n'
    for pdu in GLGet('TxPdu'):
        cstr += 'const ComSignal_type * const %s_TX_SignalRefs[] = {\n'%(GAGet(pdu,'name'))
        for sig in GLGet(pdu,'SignalRefs'):
            cstr += '\t&ComSignal[ COM_SID_%s ],\n'%(GAGet(sig,'name'))
        cstr += '\tNULL\n};\n'        
    fp.write("""
//IPdu signal lists.
%s    
    """%(cstr))
    cstr = ''
    for pdu in GLGet('RxPdu'):
        cstr += """
    {
        .ComIPduCallout =  NULL,
        .ArcIPduOutgoingId =  PDUR_%s_RX,
        .ComIPduSignalProcessing =  IMMEDIATE,
        .ComIPduSize =  8,
        .ComIPduDirection =  RECEIVE,
        .ComIPduGroupRef =  COM_DEFAULT_IPDU_GROUP, // -> default
        .ComTxIPdu ={
            .ComTxIPduMinimumDelayFactor =  1,
            .ComTxIPduUnusedAreasDefault =  0,
            .ComTxModeTrue ={
                .ComTxModeMode =   DIRECT,
                .ComTxModeNumberOfRepetitions =   0,
                .ComTxModeRepetitionPeriodFactor =   10,
                .ComTxModeTimeOffsetFactor =   0,
                .ComTxModeTimePeriodFactor =   10, // Period: in Tick of MainFunction
            },
        },
        .ComIPduDataPtr =  %s_RX_IPduBuffer,
        .ComIPduDeferredDataPtr =  NULL, // TODO: if Processing is DEFERRED, config this buffer, please
        .ComIPduSignalRef =  %s_RX_SignalRefs,
        .ComIPduDynSignalRef =  NULL,
        .Com_Arc_EOL =  FALSE,
    },\n"""%(GAGet(pdu,'name'),GAGet(pdu,'name'),GAGet(pdu,'name'))
    id = 0
    for pdu in GLGet('TxPdu'):
        cstr += """
    {
        .ComIPduCallout =  NULL,
        .ArcIPduOutgoingId =  PDUR_%s_TX,
        .ComIPduSignalProcessing =  IMMEDIATE,
        .ComIPduSize =  8,
        .ComIPduDirection =  SEND,
        .ComIPduGroupRef =  COM_DEFAULT_IPDU_GROUP, // -> default
        .ComTxIPdu ={
            .ComTxIPduMinimumDelayFactor =  1,
            .ComTxIPduUnusedAreasDefault =  0,
            .ComTxModeTrue ={
                .ComTxModeMode =   PERIODIC,    // TODO:
                .ComTxModeNumberOfRepetitions =   0,
                .ComTxModeRepetitionPeriodFactor =   10,
                .ComTxModeTimeOffsetFactor =   0,
                .ComTxModeTimePeriodFactor =   10, // Period: in Tick of MainFunction
            },
        },
        .ComIPduDataPtr =  %s_TX_IPduBuffer,
        .ComIPduDeferredDataPtr =  NULL,    // TODO: if Processing is DEFERRED, config this buffer, please
        .ComIPduSignalRef =  %s_TX_SignalRefs,
        .ComIPduDynSignalRef =  NULL,
        .Com_Arc_EOL =  FALSE,
    },\n"""%(GAGet(pdu,'name'),GAGet(pdu,'name'),GAGet(pdu,'name'))    
    fp.write("""
//I-PDU definitions
const ComIPdu_type ComIPdu[] = {
%s
    {
        .Com_Arc_EOL =  TRUE
    }
};

const Com_ConfigType ComConfiguration = {
    .ComConfigurationId =  1,
    .ComIPdu =  ComIPdu,
    .ComIPduGroup =  ComIPduGroup,
    .ComSignal =  ComSignal,
#if(COM_N_GROUP_SIGNALS > 0)
    .ComGroupSignal =  ComGroupSignal
#else
    .ComGroupSignal =  NULL
#endif
};\n\n"""%(cstr))
    cstr = 'Com_Arc_IPdu_type Com_Arc_IPdu[] = {\n'
    for pdu in GLGet('RxPdu')+GLGet('TxPdu'):
        cstr += """
    { // %s
        .Com_Arc_TxIPduTimers ={
            .ComTxIPduNumberOfRepetitionsLeft =  0,
            .ComTxModeRepetitionPeriodTimer =  0,
            .ComTxIPduMinimumDelayTimer =  0,
            .ComTxModeTimePeriodTimer =  0
        },
        .Com_Arc_IpduStarted =  0
    },\n"""%(GAGet(pdu,'name'))
    cstr += '};\n\n'
    cstr += 'Com_Arc_Signal_type Com_Arc_Signal[] = {\n'
    for sig in GLGet('Signal'):
        cstr += """
    { // %s
        .Com_Arc_DeadlineCounter =  0,
        .ComSignalUpdated =  0,
    },\n"""%(GAGet(sig,'name'))
    cstr += '};\n\n'   
    fp.write(cstr)
    fp.write("""
#if 0    
#if(COM_N_GROUP_SIGNALS > 0)
Com_Arc_GroupSignal_type Com_Arc_GroupSignal[COM_N_GROUP_SIGNALS];
#endif
#endif // 0

const Com_Arc_Config_type Com_Arc_Config = {
    .ComIPdu =  Com_Arc_IPdu,
    .ComSignal =  Com_Arc_Signal,
#if(COM_N_GROUP_SIGNALS > 0)
    .ComGroupSignal =  Com_Arc_GroupSignal
#else
    .ComGroupSignal =  NULL
#endif
};    
    """)
    fp.close()
    
def GenPy():

    # =========================  PduR_Cfg.h ==================
    fp = open('../../tools/can/ComApi.py','w')
    fp.write('\n# Gen by easyCom\n')
    fp.write("""
import threading,time
import sys
import socket
import UserString 

def lDebug(stri):
    print stri 
    \n""")
    fp.write('cPduTx=0\ncPduRx=1\n')
    cstr = '# Id Ref of Pdu\n'
    id = 0
    for pdu in GLGet('RxPdu'):
        cstr += 'COM_%s_RX=%s\n'%(GAGet(pdu,'name'),id)
        id += 1
    for pdu in GLGet('TxPdu'):
        cstr += 'COM_%s_TX=%s\n'%(GAGet(pdu,'name'),id)
        id += 1
    fp.write(cstr)
    cstr = '# Id Ref of Signal\n'
    id = 0
    for sig in GLGet('Signal'):
        cstr += 'COM_SID_%s=%s\n'%(GAGet(sig,'name'),id)
        id += 1
    fp.write(cstr)
    cstr = '# Pdu Obj = [id,[data],type]\n'
    cstr += 'cPduCanId=0\ncPduData=1\ncPduType=2\n'
    cstr += 'PduObjList = [ \\\n'
    for pdu in GLGet('RxPdu'):
        cstr += '\t[%s,[0,0,0,0,0,0,0,0],cPduRx], #%s\n'%(GAGet(pdu,'id'),GAGet(pdu,'name'))
    for pdu in GLGet('TxPdu'):
        cstr += '\t[%s,[0,0,0,0,0,0,0,0],cPduTx], #%s\n'%(GAGet(pdu,'id'),GAGet(pdu,'name'))
    cstr += ']\n'
    fp.write(cstr)
    fp.write("""
def __UpdateValue(pduId,SigStart,SigSize,SigValue):
    global PduObjList
    BA = 0
    bitsize = SigSize
    start   = SigStart
    value   = SigValue
    data    = PduObjList[pduId][cPduData]
    pos = start/8
    CrossB = (SigSize+7)/8
    if(SigStart>=(pos*8) and (SigStart+SigSize)<=(pos+CrossB)*8):
        pass
    else:
        CrossB += 1
    for i in range(0,CrossB):
        start   += BA     # bit accessed in this cycle
        bitsize -= BA
        pos = start/8
        offset = start%8 
        if((8-offset) > bitsize):
            BA =  bitsize
        else:
            BA = (8-offset)
        BM = ((1<<BA)-1)<<offset
        data[pos] &=  ~BM
        data[pos] |=  BM&(value<<offset)
        value = value>>(bitsize-BA)
    
def __ReadValue(pduId,SigStart,SigSize):
    global PduObjList
    value   = 0
    data    = PduObjList[pduId][cPduData]
    pos = SigStart/8
    CrossB = (SigSize+7)/8
    if(SigStart>=(pos*8) and (SigStart+SigSize)<=(pos+CrossB)*8):
        pass
    else:
        CrossB += 1
    for i in range(0,CrossB):
        value = value+(data[pos+i]<<(8*i))
    offset = SigStart%8 
    return (value>>offset)&((1<<SigSize)-1)
    \n\n""")    
    cstr = 'def Com_SendSignal(sigId,value):\n'
    for sig in GLGet('Signal'):
        if(GAGet(sig,'msgtype') == 'RX'):
            cstr += """
    if(sigId == COM_SID_%s):
        lDebug(\'Send(%s)\')
        __UpdateValue(COM_%s_RX,%s,%s,value)
        return 0
            \n"""%(GAGet(sig,'name'),GAGet(sig,'name'),GAGet(sig,'msgname'),GAGet(sig,'start'),GAGet(sig,'size'))
    cstr += '\tprint \'Error Signal Id\'\n\treturn -1 # error id\n\n'
    fp.write(cstr)
    cstr = 'def Com_ReadSignal(sigId):\n'
    for sig in GLGet('Signal'):
        if(GAGet(sig,'msgtype') == 'RX'):
            cstr += """
    if(sigId == COM_SID_%s):
        lDebug(\'Read(%s)\')
        return __ReadValue(COM_%s_RX,%s,%s)
            \n"""%(GAGet(sig,'name'),GAGet(sig,'name'),GAGet(sig,'msgname'),GAGet(sig,'start'),GAGet(sig,'size'))
    for sig in GLGet('Signal'):
        if(GAGet(sig,'msgtype') == 'TX'):
            cstr += """
    if(sigId == COM_SID_%s):
        lDebug(\'Read(%s)\')
        return __ReadValue(COM_%s_TX,%s,%s)
            \n"""%(GAGet(sig,'name'),GAGet(sig,'name'),GAGet(sig,'msgname'),GAGet(sig,'start'),GAGet(sig,'size'))
    cstr += '\tprint \'Error Signal Id\'\n\treturn -1 # error id\n\n'
    fp.write(cstr)  
    
    cstr = ''
    id = 0
    for sig in GLGet('Signal'):  
        cstr += '%-16s=%-3s  ;  '%(GAGet(sig,'name'),id)
        id += 1
        if(id%3 ==0):
            cstr += '\n'
    fp.write("""
def ShowSignalList():
    print \"\"\"SignalIdList:
%s\\n\"\"\"
    \n"""%(cstr))
    fp.write("""

class ComServerTx(threading.Thread): 
    __txPort = 8000
    __rxPort = 60001
    def __init__(self,txPort=8000,rxPort = 60001):
        self.__txPort = txPort
        self.__rxPort = rxPort
        threading.Thread.__init__(self)
        self.start()
    def run(self):
        global PduObjList
        while(True):
            for pdu in PduObjList:
                if(pdu[cPduType] == cPduRx):
                    self.transmit(pdu[cPduCanId],pdu[cPduData])
            time.sleep(0.100)  # 100ms
            
    def transmit(self,canId,data,length=None):
        msg = UserString.MutableString("c" * 17)
        msg[0] = '%c'%((canId>>24)&0xFF)
        msg[1] = '%c'%((canId>>16)&0xFF)
        msg[2] = '%c'%((canId>>8)&0xFF)
        msg[3] = '%c'%(canId&0xFF)
        if(None == length):
            length = len(data)
        assert length <= 8
        msg[4] = '%c'%(length) #DLC
        for i in range(0,length):
            msg[5+i] = '%c'%((data[i])&0xFF)
        for i in range(length,8):
            msg[5+i] = '%c'%(0x55)
        msg[13] = '%c'%((self.__rxPort>>24)&0xFF)
        msg[14] = '%c'%((self.__rxPort>>16)&0xFF)
        msg[15] = '%c'%((self.__rxPort>>8)&0xFF)
        msg[16] = '%c'%((self.__rxPort)&0xFF)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', self.__txPort ))  
            sock.send(msg.data)
            sock.close()
        except:
            print 'ERROR: CanBusServer isn\\'t started.'     
class ComServerRx(threading.Thread): 
    __rxPort = 60001
    def __init__(self,rxPort=60001):
        self.__rxPort = rxPort
        threading.Thread.__init__(self)
        self.start()
    def receive(self,msg):
        global PduObjList
        canId = (ord(msg[0])<<24)+(ord(msg[1])<<16)+(ord(msg[2])<<8)+(ord(msg[3]))
        for pdu in PduObjList:
            if(pdu[cPduCanId] == canId and pdu[cPduType] == cPduTx):
                data = pdu[cPduData]
                for i in range(0,8):
                    data[i] = ord(msg[5+i])
                break
                print pdu
    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
        sock.bind(('127.0.0.1', self.__rxPort))  
        sock.listen(32) 
        while True:  
            try:
                connection,address = sock.accept() 
                connection.settimeout(1)
                msg = connection.recv(17)  
                connection.close()
                if(len(msg) == 17):
                    self.receive(msg)
            except socket.timeout:  
                continue  
            connection.close() 

ComServerTx(8000,60001)
ComServerRx(60001)        
    """)  
    fp.close()

