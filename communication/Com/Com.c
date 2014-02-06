/* -------------------------------- Arctic Core ------------------------------
 * Arctic Core - the open source AUTOSAR platform http://arccore.com
 *
 * Copyright (C) 2009  ArcCore AB <contact@arccore.com>
 *
 * This source code is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License version 2 as published by the
 * Free Software Foundation; See <http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt>.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
 * or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
 * for more details.
 * -------------------------------- Arctic Core ------------------------------*/


//lint -esym(960,8.7)	PC-Lint misunderstanding of Misra 8.7 for Com_SystenEndianness and endianess_test





#include <assert.h>
#include <stdlib.h>
//#include <stdio.h>
#include <string.h>
#include "Com.h"
#include "Com_Arc_Types.h"
#include "Com_Internal.h"
#include "Com_misc.h"
#include "debug.h"
#include "Cpu.h"


/* TODO: Better way to get endianness across all compilers? */
static const uint32_t endianness_test = 0xdeadbeefU;
ComSignalEndianess_type Com_SystemEndianness;


const Com_ConfigType * ComConfig;


void Com_Init(const Com_ConfigType *config ) {
	DEBUG(DEBUG_LOW, "--Initialization of COM--\n");

	ComConfig = config;

	uint8 failure = 0;

	uint32 firstTimeout;

	//lint --e(928)	PC-Lint exception Misra 11.4, Must be like this. /tojo
	uint8 endiannessByte = *(const uint8 *)&endianness_test;
	if      ( endiannessByte == 0xef ) { Com_SystemEndianness = COM_LITTLE_ENDIAN; }
	else if ( endiannessByte == 0xde ) { Com_SystemEndianness = COM_BIG_ENDIAN; }
	else {
		// No other endianness supported
		//lint --e(506)	PC-Lint exception Misra 13.7, 14.1, Allow boolean to always be false.
		assert(0);
	}

	// Initialize each IPdu
	//ComIPdu_type *IPdu;
	//Com_Arc_IPdu_type *Arc_IPdu;
	const ComSignal_type *Signal;
	const ComGroupSignal_type *GroupSignal;
	for (uint16 i = 0; !ComConfig->ComIPdu[i].Com_Arc_EOL; i++) {

		const ComIPdu_type *IPdu = GET_IPdu(i);
		Com_Arc_IPdu_type *Arc_IPdu = GET_ArcIPdu(i);
		Arc_IPdu->Com_Arc_DynSignalLength = 0;

		if (i >= COM_N_IPDUS) {
			DET_REPORTERROR(COM_MODULE_ID, COM_INSTANCE_ID, 0x01, COM_E_TOO_MANY_IPDU);
			failure = 1;
			break;
		}

		// If this is a TX and cyclic IPdu, configure the first deadline.
		if ( (IPdu->ComIPduDirection == SEND) &&
				( (IPdu->ComTxIPdu.ComTxModeTrue.ComTxModeMode == PERIODIC) || (IPdu->ComTxIPdu.ComTxModeTrue.ComTxModeMode == MIXED) )) {
			//IPdu->Com_Arc_TxIPduTimers.ComTxModeTimePeriodTimer = IPdu->ComTxIPdu.ComTxModeTrue.ComTxModeTimeOffsetFactor;
			Arc_IPdu->Com_Arc_TxIPduTimers.ComTxModeTimePeriodTimer = IPdu->ComTxIPdu.ComTxModeTrue.ComTxModeTimeOffsetFactor;
		}


		// Reset firstTimeout.
		firstTimeout = 0xffffffffu;

		// Initialize the memory with the default value.
		if (IPdu->ComIPduDirection == SEND) {
			memset((void *)IPdu->ComIPduDataPtr, IPdu->ComTxIPdu.ComTxIPduUnusedAreasDefault, IPdu->ComIPduSize);
		}

		// For each signal in this PDU.
		//Arc_IPdu->NComIPduSignalRef = 0;
		for (uint16 j = 0; (IPdu->ComIPduSignalRef != NULL) && (IPdu->ComIPduSignalRef[j] != NULL) ; j++) {
			Signal = IPdu->ComIPduSignalRef[j];
			Com_Arc_Signal_type * Arc_Signal = GET_ArcSignal(Signal->ComHandleId);

			// Configure signal deadline monitoring if used.
			if (Signal->ComTimeoutFactor > 0) {

				if (Signal->ComSignalArcUseUpdateBit) {
					// This signal uses an update bit, and hence has its own deadline monitoring.
					Arc_Signal->Com_Arc_DeadlineCounter = Signal->ComFirstTimeoutFactor; // Configure the deadline counter

				} else {
					// This signal does not use an update bit, and should therefore use per I-PDU deadline monitoring.
					if (firstTimeout > Signal->ComFirstTimeoutFactor) {
						firstTimeout = Signal->ComFirstTimeoutFactor;
					}
				}
			}

			// Clear update bits
			if (Signal->ComSignalArcUseUpdateBit) {
				CLEARBIT(IPdu->ComIPduDataPtr, Signal->ComUpdateBitPosition);
			}

			// If this signal is a signal group
			if (Signal->Com_Arc_IsSignalGroup) {

				// For each group signal of this signal group.
				for(uint8 h = 0; Signal->ComGroupSignal[h] != NULL; h++) {
					GroupSignal = Signal->ComGroupSignal[h];
					Com_Arc_GroupSignal_type *Arc_GroupSignal = GET_ArcGroupSignal(GroupSignal->ComHandleId);
					// Set pointer to shadow buffer
					Arc_GroupSignal->Com_Arc_ShadowBuffer = (void *)Signal->Com_Arc_ShadowBuffer;
					// Initialize shadowbuffer.
					Com_UpdateShadowSignal(GroupSignal->ComHandleId, GroupSignal->ComSignalInitValue);
				}
				// Initialize group signal data from shadowbuffer.
				Com_CopySignalGroupDataFromShadowBufferToPdu(Signal->ComHandleId);
			} else {
				// Initialize signal data.
				Com_WriteSignalDataToPdu(Signal->ComHandleId, Signal->ComSignalInitValue);
			}
		}
		if (IPdu->ComIPduDirection == RECEIVE && IPdu->ComIPduSignalProcessing == DEFERRED) {
			// Copy the initialized pdu to deferred buffer
			memcpy(IPdu->ComIPduDeferredDataPtr,IPdu->ComIPduDataPtr,IPdu->ComIPduSize);
		}
		// Configure per I-PDU based deadline monitoring.
		for (uint16 j = 0; (IPdu->ComIPduSignalRef != NULL) && (IPdu->ComIPduSignalRef[j] != NULL); j++) {
			Signal = IPdu->ComIPduSignalRef[j];
			Com_Arc_Signal_type * Arc_Signal = GET_ArcSignal(Signal->ComHandleId);

			if ( (Signal->ComTimeoutFactor > 0) && (!Signal->ComSignalArcUseUpdateBit) ) {
				Arc_Signal->Com_Arc_DeadlineCounter = firstTimeout;
			}
		}
	}
	for (uint16 i = 0; i < COM_N_IPDUS; i++) {
		Com_BufferPduState[i].currentPosition = 0;
		Com_BufferPduState[i].locked = false;
	}

	// An error occurred.
	if (failure) {
		DEBUG(DEBUG_LOW, "--Initialization of COM failed--\n");
		//DET_REPORTERROR(COM_MODULE_ID, COM_INSTANCE_ID, 0x01, COM_E_INVALID_FILTER_CONFIGURATION);
	} else {
		DEBUG(DEBUG_LOW, "--Initialization of COM completed--\n");
	}
}


void Com_DeInit( void ) {

}

void Com_IpduGroupStart(Com_PduGroupIdType IpduGroupId,boolean Initialize) {
	(void)Initialize; // Nothing to be done. This is just to avoid Lint warning.
	for (uint16 i = 0; !ComConfig->ComIPdu[i].Com_Arc_EOL; i++) {
		if (ComConfig->ComIPdu[i].ComIPduGroupRef == IpduGroupId) {
			Com_Arc_Config.ComIPdu[i].Com_Arc_IpduStarted = 1;
		}
	}
}

void Com_IpduGroupStop(Com_PduGroupIdType IpduGroupId) {
	for (uint16 i = 0; !ComConfig->ComIPdu[i].Com_Arc_EOL; i++) {
		if (ComConfig->ComIPdu[i].ComIPduGroupRef == IpduGroupId) {
			Com_Arc_Config.ComIPdu[i].Com_Arc_IpduStarted = 0;
		}
	}
}

/**
 *
 * @param PduId
 * @param PduInfoPtr
 * @param RetryInfoPtr not supported
 * @param TxDataCntPtr
 * @return
 */
BufReq_ReturnType Com_CopyTxData(PduIdType PduId, PduInfoType* PduInfoPtr, RetryInfoType* RetryInfoPtr, PduLengthType* TxDataCntPtr) {
	imask_t state;
	BufReq_ReturnType r = BUFREQ_OK;
	const ComIPdu_type *IPdu = GET_IPdu(PduId);
	boolean dirOk = ComConfig->ComIPdu[PduId].ComIPduDirection == SEND;
	boolean sizeOk;
	(void)RetryInfoPtr; // get rid of compiler warning

	Irq_Save(state);
	sizeOk = IPdu->ComIPduSize >= Com_BufferPduState[PduId].currentPosition + PduInfoPtr->SduLength;
	Com_BufferPduState[PduId].locked = true;
	if (dirOk && sizeOk) {
		void* source = (void *)IPdu->ComIPduDataPtr;
		memcpy(PduInfoPtr->SduDataPtr,(uint8 *)source + Com_BufferPduState[PduId].currentPosition, PduInfoPtr->SduLength);
		Com_BufferPduState[PduId].currentPosition += PduInfoPtr->SduLength;
		*TxDataCntPtr = IPdu->ComIPduSize - Com_BufferPduState[PduId].currentPosition;
	} else {
		r = BUFREQ_NOT_OK;
	}
	Irq_Restore(state);
	return r;
}
BufReq_ReturnType Com_CopyRxData(PduIdType PduId, const PduInfoType* PduInfoPtr, PduLengthType* RxBufferSizePtr) {
	imask_t state;
	BufReq_ReturnType r = BUFREQ_OK;
	uint8 remainingBytes;
	boolean sizeOk;
	boolean dirOk;
	boolean lockOk;

	Irq_Save(state);

	remainingBytes = GET_IPdu(PduId)->ComIPduSize - Com_BufferPduState[PduId].currentPosition;
	sizeOk = remainingBytes >= PduInfoPtr->SduLength;
    dirOk = GET_IPdu(PduId)->ComIPduDirection == RECEIVE;
	lockOk = isPduBufferLocked(PduId);
	if (dirOk && lockOk && sizeOk) {
		memcpy((void *)((uint8 *)GET_IPdu(PduId)->ComIPduDataPtr+Com_BufferPduState[PduId].currentPosition), PduInfoPtr->SduDataPtr, PduInfoPtr->SduLength);
		Com_BufferPduState[PduId].currentPosition += PduInfoPtr->SduLength;
		*RxBufferSizePtr = GET_IPdu(PduId)->ComIPduSize - Com_BufferPduState[PduId].currentPosition;
	} else {
		r = BUFREQ_NOT_OK;
	}
	Irq_Restore(state);
	return r;
}

static void Com_SetDynSignalLength(PduIdType ComRxPduId,PduLengthType TpSduLength) {
	const ComIPdu_type *IPdu = GET_IPdu(ComRxPduId);
	if (IPdu->ComIPduDynSignalRef == 0) {
		return;
	}
	const ComSignal_type * const dynSignal = IPdu->ComIPduDynSignalRef;
	Com_Arc_IPdu_type *Arc_IPdu = GET_ArcIPdu(ComRxPduId);
	Arc_IPdu->Com_Arc_DynSignalLength = TpSduLength - (dynSignal->ComBitPosition/8);
	return;
}

BufReq_ReturnType Com_StartOfReception(PduIdType ComRxPduId, PduLengthType TpSduLength, PduLengthType* RxBufferSizePtr) {
	PduLengthType ComIPduSize;
	imask_t state;
	BufReq_ReturnType r = BUFREQ_OK;
	Com_Arc_IPdu_type *Arc_IPdu = GET_ArcIPdu(ComRxPduId);

	Irq_Save(state);
	if (Arc_IPdu->Com_Arc_IpduStarted) {
		if (GET_IPdu(ComRxPduId)->ComIPduDirection == RECEIVE) {
			if (!Com_BufferPduState[ComRxPduId].locked) {
				ComIPduSize = GET_IPdu(ComRxPduId)->ComIPduSize;
				if (ComIPduSize >= TpSduLength) {
					Com_BufferPduState[ComRxPduId].locked = true;
					*RxBufferSizePtr = ComIPduSize;
					Com_SetDynSignalLength(ComRxPduId,TpSduLength);
				} else {
					r = BUFREQ_OVFL;
				}
			} else {
				r = BUFREQ_BUSY;
			}
		}
	} else {
		r = BUFREQ_NOT_OK;
	}
	Irq_Restore(state);
	return r;
}
#if defined(__GTK__)
#include <gtk/gtk.h>
static GtkWidget* pEntryList[COM_N_SIGNALS];
static uint8 Buffer[COM_N_IPDUS][8];
static uint32 Timer[COM_N_IPDUS];
static void Update(uint32 IpduID,uint32 SigStart,uint32 SigSize,uint32 SigValue)
{

    int BA = 0;
    int bitsize = SigSize;
    int start   = SigStart;
    int value   = SigValue;
    uint8* data = Buffer[IpduID];
    int pos = start/8;
    int CrossB = (SigSize+7)/8;
    if(SigStart>=(pos*8) && (SigStart+SigSize)<=(pos+CrossB)*8)
    {
    }
    else
    {
        CrossB += 1;
    }
    for(int i=0;i<CrossB;i++)
    {
        start   += BA;   // bit accessed in this cycle
        bitsize -= BA;
        pos = start/8;
        int offset = start%8;
        if((8-offset) > bitsize){
            BA =  bitsize;
        }
        else
        {
            BA = (8-offset);
        }
        int BM = ((1<<BA)-1)<<offset;
        data[pos] &=  ~BM;
        data[pos] |=  BM&(value<<offset);
        value = value>>(bitsize-BA);
    }
}
static uint32 Read(const ComIPdu_type *IPdu,int SigStart,int SigSize)
{
	int value   = 0;
	uint8* data    = IPdu->ComIPduDataPtr;
	int pos = SigStart/8;
	int CrossB = (SigSize+7)/8;
	if(SigStart>=(pos*8) && (SigStart+SigSize)<=(pos+CrossB)*8)
	{
	}
	else
	{
		CrossB += 1;
	}
	for(int i=0;i<CrossB;i++)
	{
		value = value+(data[pos+i]<<(8*i));
	}
	int offset = SigStart%8;
	return (value>>offset)&((1<<SigSize)-1);
}
static void Refresh(const ComIPdu_type *IPdu)
{
	for (uint16 j = 0; (IPdu->ComIPduSignalRef != NULL) && (IPdu->ComIPduSignalRef[j] != NULL) ; j++) {
		const ComSignal_type * Signal = IPdu->ComIPduSignalRef[j];
		GtkWidget* pEntry = pEntryList[Signal->ComHandleId];
		gchar value[32];
		sprintf(value,"%d",Read(IPdu,Signal->ComBitPosition,Signal->ComBitSize));
		gtk_entry_set_text(GTK_ENTRY(pEntry),value);
	}
}
static void on_entry_activate(GtkEntry *entry,gpointer data)
{
	int Id = (int)(data);
	gchar* pValue = gtk_entry_get_text(entry);

	const ComSignal_type * Signal = &(ComConfig->ComSignal[Id]);

	uint32 max = (1u<<Signal->ComBitSize)-1u;

	uint32 value = atoi(pValue);

	if(value <= max)
	{
		Update(Signal->ComIPduHandleId,Signal->ComBitPosition,Signal->ComBitSize,value);
	}
	else
	{
		gchar value[32];
		gtk_entry_set_text(GTK_ENTRY(entry),value);
		Update(Signal->ComIPduHandleId,Signal->ComBitPosition,Signal->ComBitSize,max);
	}
}
extern boolean arch_is_paused(void);
static gboolean simulator(gpointer data)
{
	if( (NULL == ComConfig) ||
		(arch_is_paused()) )
	{
		return TRUE;
	}
	for (uint16 i = 0; !ComConfig->ComIPdu[i].Com_Arc_EOL; i++) {
		const ComIPdu_type *IPdu = GET_IPdu(i);
		if (IPdu->ComIPduDirection == SEND) {
			Refresh(IPdu);
		}
		else
		{
			if(0u==Timer[i])
			{
				PduInfoType pdu;
				pdu.SduDataPtr = Buffer[i];
				pdu.SduLength  = 8;
				Com_RxIndication(i,&pdu);
				Timer[i] = IPdu->ComTxIPdu.ComTxModeTrue.ComTxModeTimePeriodFactor*2;
			}
			else
			{
				Timer[i]--;
			}
		}
	}

	return TRUE;
}
static GtkWidget* ComPage(const ComIPdu_type *IPdu)
{
	GtkWidget* pGrid;
	gboolean   isSensetive = TRUE;

	pGrid = gtk_grid_new();

	if (IPdu->ComIPduDirection == SEND) {
		isSensetive = FALSE;
	}
	for (uint16 j = 0; (IPdu->ComIPduSignalRef != NULL) && (IPdu->ComIPduSignalRef[j] != NULL) ; j++) {
		const ComSignal_type * Signal = IPdu->ComIPduSignalRef[j];
		GtkWidget* pEntry = gtk_entry_new();
		pEntryList[Signal->ComHandleId] = pEntry;
		gtk_grid_attach(GTK_GRID(pGrid),gtk_label_new(Signal->name),(j%2)*2,j/2,1,1);
		gtk_grid_attach(GTK_GRID(pGrid),pEntry,(j%2)*2+1,j/2,1,1);
		gtk_entry_set_width_chars(GTK_ENTRY(pEntry),32);
		gchar value[32];
		if(Signal->ComBitSize<=8)
		{
			sprintf(value,"%d",*(uint8*)Signal->ComSignalInitValue);
			Update(Signal->ComIPduHandleId,Signal->ComBitPosition,Signal->ComBitSize,*(uint8*)Signal->ComSignalInitValue);
		}
		else if(Signal->ComBitSize<=16)
		{
			sprintf(value,"%d",*(uint16*)Signal->ComSignalInitValue);
			Update(Signal->ComIPduHandleId,Signal->ComBitPosition,Signal->ComBitSize,*(uint16*)Signal->ComSignalInitValue);
		}
		else if(Signal->ComBitSize<=32)
		{
			sprintf(value,"%d",*(uint32*)Signal->ComSignalInitValue);
			Update(Signal->ComIPduHandleId,Signal->ComBitPosition,Signal->ComBitSize,*(uint32*)Signal->ComSignalInitValue);
		}
		else
		{
			sprintf(value,"un-support type");
		}
		gtk_entry_set_text(GTK_ENTRY(pEntry),value);
		gtk_widget_set_sensitive(GTK_WIDGET(pEntry),isSensetive);

		if(isSensetive)
		{
			g_signal_connect(G_OBJECT (pEntry), "activate",
				G_CALLBACK(on_entry_activate) , (gpointer)(Signal->ComHandleId));
		}
	}

	return pGrid;
}
GtkWidget* Com(void)
{
	GtkWidget* pNotebook;

	ComConfig = &ComConfiguration;

	pNotebook = gtk_notebook_new ();
	for (uint16 i = 0; !ComConfig->ComIPdu[i].Com_Arc_EOL; i++) {
		const ComIPdu_type *IPdu = GET_IPdu(i);
		Com_Arc_IPdu_type *Arc_IPdu = GET_ArcIPdu(i);
		gtk_notebook_append_page (GTK_NOTEBOOK(pNotebook),ComPage(IPdu),gtk_label_new(IPdu->name));
	}

	g_timeout_add(5,simulator,NULL);
	memset(Timer,0,sizeof(Timer));
	ComConfig = NULL;
	return pNotebook;
}
#endif
