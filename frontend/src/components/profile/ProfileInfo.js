import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Card, Button, Input } from '../common/ui';
import TwilioNumberPurchase from './TwilioNumberPurchase';

const ProfileInfo = () => {
    const { user, updateUserProfile } = useAuth();
    
    const [editMode, setEditMode] = useState(false);
    const [formData, setFormData] = useState({
        name: user?.name || '',
        email: user?.email || '',
        phone_number: user?.phone_number || ''
    });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(false);

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);
        setSuccess(false);

        try {
            await updateUserProfile(formData);
            setSuccess(true);
            setEditMode(false);
        } catch (err) {
            setError(err.message || 'Failed to update profile. Please try again later.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleCancel = () => {
        setFormData({
            name: user?.name || '',
            email: user?.email || '',
            phone_number: user?.phone_number || ''
        });
        setEditMode(false);
        setError(null);
    };

    // Show the number purchase component if user doesn't have a phone number
    const shouldShowNumberPurchase = !user?.phone_number;

    return (
        <div>
            <Card className="p-5 mb-6">
                <h2 className="text-xl font-semibold mb-4">Your Profile</h2>
                
                {success && (
                    <div className="bg-green-100 text-green-700 p-3 rounded-md mb-4">
                        Profile updated successfully!
                    </div>
                )}
                
                {error && (
                    <div className="bg-red-100 text-red-700 p-3 rounded-md mb-4">
                        {error}
                    </div>
                )}
                
                {editMode ? (
                    <form onSubmit={handleSubmit}>
                        <div className="mb-4">
                            <Input
                                label="Name"
                                name="name"
                                value={formData.name}
                                onChange={handleChange}
                                required
                            />
                        </div>
                        
                        <div className="mb-4">
                            <Input
                                label="Email"
                                name="email"
                                type="email"
                                value={formData.email}
                                onChange={handleChange}
                                disabled
                            />
                            <p className="text-sm text-gray-500 mt-1">
                                Email cannot be changed
                            </p>
                        </div>
                        
                        <div className="mb-6">
                            <Input
                                label="Phone Number"
                                name="phone_number"
                                value={formData.phone_number}
                                onChange={handleChange}
                                disabled={true}
                            />
                            <p className="text-sm text-gray-500 mt-1">
                                Use the Twilio Number Purchase section to update your phone number
                            </p>
                        </div>
                        
                        <div className="flex space-x-3">
                            <Button
                                type="submit"
                                isLoading={isLoading}
                            >
                                Save Changes
                            </Button>
                            <Button
                                type="button"
                                variant="outline"
                                onClick={handleCancel}
                            >
                                Cancel
                            </Button>
                        </div>
                    </form>
                ) : (
                    <div>
                        <div className="mb-4">
                            <h3 className="text-sm font-medium text-gray-500">Name</h3>
                            <p>{user?.name || 'Not set'}</p>
                        </div>
                        
                        <div className="mb-4">
                            <h3 className="text-sm font-medium text-gray-500">Email</h3>
                            <p>{user?.email || 'Not set'}</p>
                        </div>
                        
                        <div className="mb-6">
                            <h3 className="text-sm font-medium text-gray-500">Phone Number</h3>
                            <p>{user?.phone_number || 'Not set'}</p>
                        </div>
                        
                        <Button onClick={() => setEditMode(true)}>
                            Edit Profile
                        </Button>
                    </div>
                )}
            </Card>
            
            {shouldShowNumberPurchase && <TwilioNumberPurchase />}
        </div>
    );
};

export default ProfileInfo; 