/**
 * useCancellation Hook
 * 
 * Manages cancellation modal state and orchestrates the cancellation flow.
 */

import { useState, useCallback } from 'react'

interface CancellationState {
  isOpen: boolean
  step: 'impact' | 'reason' | 'offer' | 'confirmation'
  selectedReason: string | null
  isCancelled: boolean
  error: string | null
}

export function useCancellation() {
  const [state, setState] = useState<CancellationState>({
    isOpen: false,
    step: 'impact',
    selectedReason: null,
    isCancelled: false,
    error: null,
  })

  const openCancellationModal = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isOpen: true,
      error: null,
    }))
  }, [])

  const closeCancellationModal = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isOpen: false,
    }))
  }, [])

  const handleCancellationComplete = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isOpen: false,
      isCancelled: true,
      step: 'impact',
      selectedReason: null,
    }))
  }, [])

  const resetCancellationState = useCallback(() => {
    setState({
      isOpen: false,
      step: 'impact',
      selectedReason: null,
      isCancelled: false,
      error: null,
    })
  }, [])

  return {
    ...state,
    openCancellationModal,
    closeCancellationModal,
    handleCancellationComplete,
    resetCancellationState,
  }
}
