import Header from '@/components/Header';
import Hero from '@/components/Hero';
import Problems from '@/components/Problems';
import Services from '@/components/Services';
import SlackIntegration from '@/components/SlackIntegration';
import DataProcess from '@/components/DataProcess';
import TechnicalApproach from '@/components/TechnicalApproach';
import About from '@/components/About';
import Pricing from '@/components/Pricing';
import Contact from '@/components/Contact';
import Footer from '@/components/Footer';

export default function Home() {
  return (
    <div className="min-h-screen bg-black">
      <Header />
      <main>
        <Hero />
        <Problems />
        <Services />
        <SlackIntegration />
        <DataProcess />
        <TechnicalApproach />
        <About />
        <Pricing />
        <Contact />
      </main>
      <Footer />
    </div>
  );
}
