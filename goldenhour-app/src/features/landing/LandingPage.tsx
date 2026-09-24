import React, { useEffect } from 'react';
import { HeroSection } from './sections/HeroSection';
import { ProblemSection } from './sections/ProblemSection';
import { WasteStorySection } from './sections/WasteStorySection';
import { HowItWorksSection } from './sections/HowItWorksSection';
import { DonorSection } from './sections/DonorSection';
import { ShelterSection } from './sections/ShelterSection';
import { DriverSection } from './sections/DriverSection';
import { PipelineSection } from './sections/PipelineSection';
import { ImpactSection } from './sections/ImpactSection';
import { FAQSection } from './sections/FAQSection';
import { CTASection } from './sections/CTASection';
import { FooterSection } from './sections/FooterSection';
import { useReveal } from '../../hooks/useReveal';

export const LandingPage: React.FC = () => {
  useReveal();

  useEffect(() => {
    // Add loaded classes for hero entrance animations matching reference HTML
    document.body.classList.add('hero-loaded');
    return () => {
      document.body.classList.remove('hero-loaded');
    };
  }, []);

  return (
    <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <HeroSection />
      <ProblemSection />
      <WasteStorySection />
      <HowItWorksSection />
      <DonorSection />
      <ShelterSection />
      <DriverSection />
      <PipelineSection />
      <ImpactSection />
      <FAQSection />
      <CTASection />
      <FooterSection />
    </main>
  );
};
