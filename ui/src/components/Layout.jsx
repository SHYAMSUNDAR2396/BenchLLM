import Sidebar from './Sidebar';
import Toast from './Toast';

export default function Layout({ title, children, headerRight }) {
  return (
    <div className="bg-background text-on-surface min-h-screen">
      <Sidebar />
      <header className="fixed top-0 right-0 left-[240px] h-16 bg-background border-b border-outline-variant flex items-center justify-between px-gutter z-40">
        <h2 className="font-headline-sm text-headline-sm text-on-surface">{title}</h2>
        <div className="flex items-center gap-gutter">{headerRight}</div>
      </header>
      <main className="ml-[240px] mt-16 min-h-[calc(100vh-64px)]">{children}</main>
      <Toast />
    </div>
  );
}
