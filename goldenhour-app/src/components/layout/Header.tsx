import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useSessionStore } from '../../store/session';
import { Button } from '../ui/Button';
import styles from './Header.module.css';

export const Header: React.FC = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { user, clearSession } = useSessionStore();

  const [scrolled, setScrolled] = useState(false);
  const [scrollProgress, setScrollProgress] = useState(0);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const currentScroll = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      setScrolled(currentScroll > 20);
      setScrollProgress(docHeight > 0 ? (currentScroll / docHeight) * 100 : 0);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const toggleLanguage = () => {
    const nextLang = i18n.language.startsWith('hi') ? 'en' : 'hi';
    i18n.changeLanguage(nextLang);
  };

  const isLanding = location.pathname === '/';

  return (
    <>
      {/* Scroll progress bar */}
      <div
        className={styles.progressBar}
        style={{ width: `${scrollProgress}%` }}
        role="progressbar"
        aria-valuenow={Math.round(scrollProgress)}
      />

      <header className={`${styles.header} ${scrolled ? styles.scrolled : ''}`}>
        <div className={`wrap ${styles.headerInner}`}>
          {/* Logo */}
          <Link to="/" className={styles.brand} aria-label="GoldenHour Home">
            <span className={styles.brandMark}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2.5" />
                <path d="M12 6V12L16 14" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
              </svg>
            </span>
            <span className={styles.brandText}>
              Golden<strong>Hour</strong>
            </span>
          </Link>

          {/* Center Navigation */}
          <nav className={styles.nav}>
            {isLanding ? (
              <>
                <a href="#how-it-works" className={styles.navLink}>{t('nav.howItWorks', 'How it works')}</a>
                <a href="#problem" className={styles.navLink}>{t('nav.theClock', 'The Clock')}</a>
                <a href="#impact" className={styles.navLink}>{t('nav.impact', 'Impact')}</a>
                <a href="#faq" className={styles.navLink}>{t('nav.faq', 'FAQ')}</a>
              </>
            ) : (
              <>
                <Link to="/" className={styles.navLink}>Home</Link>
                <Link to="/donor" className={`${styles.navLink} ${location.pathname.startsWith('/donor') ? styles.active : ''}`}>Donor</Link>
                <Link to="/org" className={`${styles.navLink} ${location.pathname.startsWith('/org') ? styles.active : ''}`}>Shelter</Link>
                <Link to="/driver" className={`${styles.navLink} ${location.pathname.startsWith('/driver') ? styles.active : ''}`}>Driver</Link>
                <Link to="/ops" className={`${styles.navLink} ${location.pathname.startsWith('/ops') ? styles.active : ''}`}>Ops Console</Link>
              </>
            )}
          </nav>

          {/* Right actions */}
          <div className={styles.actions}>
            {/* Language toggle */}
            <button
              type="button"
              className={styles.langBtn}
              onClick={toggleLanguage}
              title="Toggle Language"
            >
              {i18n.language.startsWith('hi') ? '🇮🇳 HI' : '🇬🇧 EN'}
            </button>

            {/* Quick Demo Switcher */}
            <div className={styles.demoPills}>
              <Link to="/donor" className={styles.rolePill} title="Donor Portal">Donor</Link>
              <Link to="/org" className={styles.rolePill} title="Shelter Portal">Shelter</Link>
              <Link to="/driver" className={styles.rolePill} title="Driver App">Driver</Link>
              <Link to="/ops" className={`${styles.rolePill} ${styles.opsPill}`} title="Ops Live Console">Ops</Link>
            </div>

            {user ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span className={styles.userBadge}>{user.name} ({user.role})</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    clearSession();
                    navigate('/');
                  }}
                >
                  Logout
                </Button>
              </div>
            ) : (
              <Button
                variant="primary"
                size="sm"
                arrow
                onClick={() => navigate('/auth')}
              >
                Sign In
              </Button>
            )}

            {/* Hamburger Button for mobile */}
            <button
              type="button"
              className={styles.menuToggle}
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle mobile menu"
            >
              <span className={`${styles.bar} ${mobileMenuOpen ? styles.barOpen : ''}`} />
              <span className={`${styles.bar} ${mobileMenuOpen ? styles.barOpen : ''}`} />
            </button>
          </div>
        </div>

        {/* Mobile Dropdown Drawer */}
        {mobileMenuOpen && (
          <div className={styles.mobileDrawer}>
            <div className={styles.mobileLinks}>
              <Link to="/" onClick={() => setMobileMenuOpen(false)}>Home</Link>
              <Link to="/donor" onClick={() => setMobileMenuOpen(false)}>Donor App</Link>
              <Link to="/org" onClick={() => setMobileMenuOpen(false)}>Shelter App</Link>
              <Link to="/driver" onClick={() => setMobileMenuOpen(false)}>Driver App</Link>
              <Link to="/ops" onClick={() => setMobileMenuOpen(false)}>Ops Console</Link>
              <div className={styles.mobileDivider} />
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0' }}>
                <span>Language</span>
                <button type="button" onClick={toggleLanguage} className={styles.langBtn}>
                  {i18n.language.startsWith('hi') ? 'हिंदी' : 'English'}
                </button>
              </div>
            </div>
          </div>
        )}
      </header>
    </>
  );
};
