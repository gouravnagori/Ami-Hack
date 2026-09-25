import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useSessionStore } from '../../store/session';
import { Button } from '../ui/Button';
import { AiAssistantModal } from '../ai/AiAssistantModal';
import styles from './Header.module.css';

export const Header: React.FC = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { user, clearSession } = useSessionStore();

  const [scrolled, setScrolled] = useState(false);
  const [scrollProgress, setScrollProgress] = useState(0);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [rolesMenuOpen, setRolesMenuOpen] = useState(false);
  const [aiModalOpen, setAiModalOpen] = useState(false);
  const rolesMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleScroll = () => {
      const currentScroll = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      setScrolled(currentScroll > 15);
      setScrollProgress(docHeight > 0 ? (currentScroll / docHeight) * 100 : 0);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Close roles dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (rolesMenuRef.current && !rolesMenuRef.current.contains(e.target as Node)) {
        setRolesMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleLanguage = () => {
    const nextLang = i18n.language.startsWith('hi') ? 'en' : 'hi';
    i18n.changeLanguage(nextLang);
  };

  const isLanding = location.pathname === '/';

  return (
    <>
      {/* Scroll progress bar - only visible when scrolled */}
      <div
        className={styles.progressBar}
        style={{
          width: `${scrollProgress}%`,
          opacity: scrollProgress > 1 ? 1 : 0,
        }}
        role="progressbar"
        aria-valuenow={Math.round(scrollProgress)}
      />

      <header className={`${styles.header} ${scrolled ? styles.scrolled : ''}`}>
        <div className={`wrap ${styles.headerInner}`}>
          {/* Logo */}
          <Link to="/" className={styles.brand} aria-label="GoldenHour Home">
            <span className={styles.brandMark}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
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
                <a href="#problem" className={styles.navLink}>{t('nav.theClock', 'The clock')}</a>
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
                <Link to="/profile" className={`${styles.navLink} ${location.pathname.startsWith('/profile') ? styles.active : ''}`}>Profile</Link>
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

            {/* Groq AI Assistant Button */}
            <button
              type="button"
              className={styles.aiBtn}
              onClick={() => setAiModalOpen(true)}
              title="GoldenHour AI Assistant"
            >
              <span>✨ Ask AI</span>
            </button>

            {/* Quick Demo Roles Dropdown */}
            <div className={styles.rolesDropdownContainer} ref={rolesMenuRef}>
              <button
                type="button"
                className={styles.rolesDropdownTrigger}
                onClick={() => setRolesMenuOpen(!rolesMenuOpen)}
                aria-expanded={rolesMenuOpen}
              >
                <span>Jaipur Portals</span>
                <span className={styles.chevron}>{rolesMenuOpen ? '▲' : '▼'}</span>
              </button>

              {rolesMenuOpen && (
                <div className={styles.rolesMenu}>
                  <Link
                    to="/auth?role=donor"
                    className={styles.rolesMenuItem}
                    onClick={() => setRolesMenuOpen(false)}
                  >
                    <span>🍲</span>
                    <div>
                      <strong>Donor Portal</strong>
                      <small>Spice Route Kitchen</small>
                    </div>
                  </Link>

                  <Link
                    to="/auth?role=recipient"
                    className={styles.rolesMenuItem}
                    onClick={() => setRolesMenuOpen(false)}
                  >
                    <span>🏠</span>
                    <div>
                      <strong>Shelter Hub</strong>
                      <small>Asha Shelter Foundation</small>
                    </div>
                  </Link>

                  <Link
                    to="/auth?role=driver"
                    className={styles.rolesMenuItem}
                    onClick={() => setRolesMenuOpen(false)}
                  >
                    <span>🛵</span>
                    <div>
                      <strong>Driver Cockpit</strong>
                      <small>Rajesh Kumar (E-Rickshaw)</small>
                    </div>
                  </Link>

                  <Link
                    to="/auth?role=admin"
                    className={`${styles.rolesMenuItem} ${styles.opsMenuItem}`}
                    onClick={() => setRolesMenuOpen(false)}
                  >
                    <span>⚡</span>
                    <div>
                      <strong>Ops Live Console</strong>
                      <small>Realtime Jaipur Telemetry</small>
                    </div>
                  </Link>

                  <div style={{ height: '1px', background: 'var(--line)', margin: '4px 0' }} />

                  <Link
                    to="/profile"
                    className={styles.rolesMenuItem}
                    onClick={() => setRolesMenuOpen(false)}
                  >
                    <span>👤</span>
                    <div>
                      <strong>Account & Profile</strong>
                      <small>View & edit user profile</small>
                    </div>
                  </Link>
                </div>
              )}
            </div>

            {user ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Link to="/profile" className={styles.profileBadgeBtn} title="My Profile & Settings">
                  <span className={styles.profileAvatarIcon}>👤</span>
                  <span>{user.name}</span>
                  <span className={styles.profileRoleTag}>{user.role}</span>
                </Link>
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
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Link
                  to="/profile"
                  className={styles.rolesDropdownTrigger}
                  style={{ textDecoration: 'none' }}
                >
                  <span>👤 Profile</span>
                </Link>
                <Button
                  variant="primary"
                  size="sm"
                  arrow
                  onClick={() => navigate('/auth')}
                >
                  Sign In
                </Button>
              </div>
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
              <Link to="/profile" onClick={() => setMobileMenuOpen(false)}>👤 My Profile</Link>
              <button
                type="button"
                className={styles.aiBtn}
                style={{ width: '100%', justifyContent: 'center', marginTop: '6px' }}
                onClick={() => {
                  setMobileMenuOpen(false);
                  setAiModalOpen(true);
                }}
              >
                ✨ Ask AI Assistant
              </button>
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

      {/* Global Groq AI Assistant Modal */}
      <AiAssistantModal isOpen={aiModalOpen} onClose={() => setAiModalOpen(false)} />
    </>
  );
};
