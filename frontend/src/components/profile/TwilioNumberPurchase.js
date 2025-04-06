import React, { useState } from 'react';
import { Button, Input, Card } from '../common/ui';
import { phoneNumberAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

const TwilioNumberPurchase = () => {
  const { updateUserProfile } = useAuth();
  const [areaCode, setAreaCode] = useState('');
  const [availableNumbers, setAvailableNumbers] = useState([]);
  const [selectedNumber, setSelectedNumber] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearchNumbers = async (e) => {
    e.preventDefault();
    setError(null);
    setAvailableNumbers([]);

    if (!areaCode || areaCode.length !== 3 || isNaN(Number(areaCode))) {
      setError('Please enter a valid 3-digit area code');
      return;
    }

    setSearchLoading(true);
    try {
      const numbers = await phoneNumberAPI.getAvailableNumbers(areaCode);
      setAvailableNumbers(numbers);
      if (numbers.length === 0) {
        setError('No available numbers found for this area code. Try another one.');
      }
    } catch (err) {
      setError('Failed to fetch available numbers. Please try again.');
      console.error(err);
    } finally {
      setSearchLoading(false);
    }
  };

  const handlePurchaseNumber = async () => {
    if (!selectedNumber) return;
    
    setLoading(true);
    setError(null);
    try {
      const result = await phoneNumberAPI.purchaseNumber(selectedNumber);
      
      // Update user profile with the new number
      await updateUserProfile({ phone_number: selectedNumber });
      
      // Reset state
      setSelectedNumber(null);
      setAvailableNumbers([]);
      setAreaCode('');
    } catch (err) {
      setError('Failed to purchase number. Please try again later.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="p-4 mb-6">
      <h3 className="text-lg font-medium mb-4">Purchase a Twilio Phone Number</h3>
      
      <form onSubmit={handleSearchNumbers} className="mb-4">
        <div className="flex gap-3">
          <Input
            label="Area Code"
            value={areaCode}
            onChange={(e) => setAreaCode(e.target.value)}
            placeholder="Enter 3-digit area code"
            className="w-full"
            maxLength={3}
          />
          <Button 
            type="submit" 
            isLoading={searchLoading}
            className="self-end"
          >
            Search
          </Button>
        </div>
      </form>

      {error && (
        <div className="text-red-500 mb-4">
          {error}
        </div>
      )}

      {availableNumbers.length > 0 && (
        <div className="mb-4">
          <h4 className="font-medium mb-2">Available Numbers</h4>
          <div className="grid grid-cols-2 gap-2">
            {availableNumbers.map(number => (
              <div 
                key={number}
                onClick={() => setSelectedNumber(number)}
                className={`p-2 border rounded cursor-pointer ${
                  selectedNumber === number 
                    ? 'bg-blue-50 border-blue-500' 
                    : 'hover:bg-gray-50'
                }`}
              >
                {number}
              </div>
            ))}
          </div>
        </div>
      )}

      {selectedNumber && (
        <div className="mt-4">
          <Button 
            onClick={handlePurchaseNumber} 
            isLoading={loading}
            variant="primary"
          >
            Purchase {selectedNumber}
          </Button>
        </div>
      )}
    </Card>
  );
};

export default TwilioNumberPurchase; 