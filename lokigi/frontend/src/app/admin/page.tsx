// page.tsx para /admin/partnerships
import React from 'react';
import PartnershipsDashboard from './PartnershipsDashboard';
import MainNav from '../components/MainNav';

export default function AdminPartnershipsPage() {
  return (
    <>
      <MainNav />
      <PartnershipsDashboard />
    </>
  );
}
