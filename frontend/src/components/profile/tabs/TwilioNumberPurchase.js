import React, { useState } from 'react';
import { Phone, X, Loader, AlertCircle, CheckCircle, Search } from 'lucide-react';
import { Card, Button, Input } from '../../common/ui';
import { phoneNumberAPI } from '../../../services/api';
import { useAuth } from '../../../contexts/AuthContext';

export const TwilioNumberPurchase = ({ onPurchaseSuccess, onCancel }) => {
  const { getCsrfToken } = useAuth();
  const [step, setStep] = useState('start'); // start, search, loading, available, purchasing, success, error
  const [areaCode, setAreaCode] = useState('');
  const [availableNumbers, setAvailableNumbers] = useState([]);
  const [selectedNumber, setSelectedNumber] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAreaCodeSearch = async (e) => {
    e?.preventDefault();
    
    if (!areaCode || areaCode.length !== 3 || isNaN(Number(areaCode))) {
      setError('Please enter a valid 3-digit area code');
      return;
    }
    
    try {
      setStep('loading');
      setIsLoading(true);
      setError(null);
      
      const response = await phoneNumberAPI.getAvailableNumbers(areaCode);
      const numbersArray = response.numbers; 
      
      if (!numbersArray || numbersArray.length === 0) {
        throw new Error('No available numbers found for this area code');
      }
      
      setAvailableNumbers(numbersArray);
      setStep('available');
    } catch (err) {
      console.error('Error fetching available numbers:', err);
      setError(err.message || 'Failed to fetch available numbers');
      setStep('error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNumberSelection = (number) => {
    setSelectedNumber(number);
  };

  const handlePurchase = async () => {
    if (!selectedNumber) return;
    
    const csrfToken = getCsrfToken();
    if (!csrfToken) {
        setError("Security token missing. Please log in again.");
        setStep('error');
        return;
    }

    try {
      setStep('purchasing');
      setIsLoading(true);
      setError(null);
      
      await phoneNumberAPI.buyNumber(selectedNumber, csrfToken);
      
      setStep('success');
      onPurchaseSuccess(selectedNumber);
    } catch (err) {
      console.error('Error purchasing number:', err);
      setError(err.message || 'Failed to purchase number');
      setStep('error');
    } finally {
      setIsLoading(false);
    }
  };

  const renderStartStep = () => (
    <div className="text-center py-6">
      <Phone className="w-12 h-12 mx-auto text-blue-600 mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        Get Your Assistant Phone Number
      </h3>
      <p className="text-gray-500 mb-6">
        Your AI assistant needs a phone number to screen your calls.
        We'll help you select and set up a number.
      </p>
      <Button 
        onClick={() => setStep('search')}
        className="w-full sm:w-auto"
      >
        Browse Available Numbers
      </Button>
    </div>
  );
  
  const renderSearch = () => (
    <div className="py-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">
          Search for Phone Numbers
        </h3>
        <button 
          onClick={onCancel}
          className="text-gray-400 hover:text-gray-500"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
      
      <form onSubmit={handleAreaCodeSearch} className="mb-4">
        <div className="mb-4">
          <Input
            label="Area Code"
            value={areaCode}
            onChange={(e) => setAreaCode(e.target.value)}
            placeholder="Enter 3-digit area code"
            maxLength={3}
          />
          <p className="mt-1 text-sm text-gray-500">
            Enter a 3-digit US area code to find available numbers
          </p>
        </div>
        
        {error && (
          <div className="mb-4 text-red-500 text-sm">
            {error}
          </div>
        )}
        
        <div className="flex justify-end space-x-3">
          <Button 
            onClick={onCancel}
            variant="outline"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={isLoading}
          >
            <Search className="w-4 h-4 mr-2" />
            Search Numbers
          </Button>
        </div>
      </form>
    </div>
  );

  const renderAvailableNumbers = () => (
    <div className="py-2">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">
          Select a Phone Number
        </h3>
        <button 
          onClick={onCancel}
          className="text-gray-400 hover:text-gray-500"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
      
      <div className="space-y-2 max-h-64 overflow-y-auto mb-4">
        {Array.isArray(availableNumbers) && availableNumbers.map((numberData) => {
          const number = typeof numberData === 'object' && numberData.phone_number ? numberData.phone_number : numberData;
          const friendlyName = typeof numberData === 'object' && numberData.friendly_name ? numberData.friendly_name : number;
          
          return (
            <div 
              key={number}
              className={`border rounded p-3 cursor-pointer transition-colors ${
                selectedNumber === number 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-200 hover:bg-gray-50'
              }`}
              onClick={() => handleNumberSelection(number)}
            >
              <div className="flex justify-between items-center">
                <div className="font-medium">{friendlyName}</div>
                {selectedNumber === number && (
                  <CheckCircle className="w-5 h-5 text-blue-500" />
                )}
              </div>
            </div>
          );
        })}
      </div>
      
      <div className="flex justify-end space-x-3">
        <Button 
          onClick={() => setStep('search')}
          variant="outline"
        >
          Back to Search
        </Button>
        <Button
          onClick={handlePurchase}
          disabled={!selectedNumber || isLoading}
        >
          {isLoading ? (
            <>
              <Loader className="w-4 h-4 mr-2 animate-spin" />
              Processing...
            </>
          ) : (
            'Purchase This Number'
          )}
        </Button>
      </div>
    </div>
  );

  const renderSuccess = () => (
    <div className="text-center py-6">
      <CheckCircle className="w-12 h-12 mx-auto text-green-500 mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        Number Purchase Successful!
      </h3>
      <p className="text-gray-500 mb-6">
        Your new assistant number is set up and ready to use.
      </p>
      <Button 
        onClick={onCancel}
        className="w-full sm:w-auto"
      >
        Done
      </Button>
    </div>
  );

  const renderError = () => (
    <div className="text-center py-6">
      <AlertCircle className="w-12 h-12 mx-auto text-red-500 mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        Something Went Wrong
      </h3>
      <p className="text-red-500 mb-6">
        {error || 'Failed to process your request. Please try again.'}
      </p>
      <div className="flex justify-center space-x-3">
        <Button 
          onClick={onCancel}
          variant="outline"
        >
          Cancel
        </Button>
        <Button 
          onClick={() => setStep('search')}
        >
          Try Again
        </Button>
      </div>
    </div>
  );

  return (
    <Card>
      {step === 'start' && renderStartStep()}
      {step === 'search' && renderSearch()}
      {step === 'loading' && (
        <div className="text-center py-12">
          <Loader className="w-12 h-12 mx-auto text-blue-500 animate-spin" />
          <p className="mt-4 text-gray-500">Loading available phone numbers...</p>
        </div>
      )}
      {step === 'available' && renderAvailableNumbers()}
      {step === 'purchasing' && (
        <div className="text-center py-12">
          <Loader className="w-12 h-12 mx-auto text-blue-500 animate-spin" />
          <p className="mt-4 text-gray-500">Purchasing your number...</p>
        </div>
      )}
      {step === 'success' && renderSuccess()}
      {step === 'error' && renderError()}
    </Card>
  );
}; 