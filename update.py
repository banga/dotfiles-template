import filecmp
import os
import subprocess
import shlex
import shutil
import sys


HOME_DIR = os.getenv("HOME")
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
NVM_DIR = os.path.join(HOME_DIR, ".nvm")
OH_MY_ZSH_DIR = os.path.join(HOME_DIR, ".oh-my-zsh")
BREW_DIR = "/usr/local"
DRY_RUN = False
HYPERLOCAL_SHRC = ".hyperlocal.shrc"


def is_linked(src_path, dest_path):
    try:
        return os.readlink(dest_path) == src_path
    except OSError:
        pass
    return False


def run_silent(command):
    return subprocess.run(
        shlex.split(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)


def run(command):
    return subprocess.run(shlex.split(command))


def run_shell(command):
    return subprocess.run(command, shell=True)


class Requirement(object):
    def is_satisfied(self):
        raise NotImplementedError()

    def install(self):
        raise NotImplementedError()

    def __str__(self):
        return self.__class__.__name__


class SymlinkRequirement(Requirement):
    def _get_paths():
        # Should yield (src, dest) pairs
        raise NotImplementedError()

    def _remove_path(self, path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

    def _link_path(self, src_path, dest_path):
        os.symlink(src_path, dest_path)

    def is_satisfied(self):
        for src_path, dest_path in self._get_paths():
            assert os.path.exists(src_path), "%s doesn't exist" % src_path
            if is_linked(src_path, dest_path):
                continue
            return False
        return True

    def install(self):
        for src_path, dest_path in self._get_paths():
            if is_linked(src_path, dest_path):
                continue
            if os.path.lexists(dest_path):
                if input("%s already exists. Replace? [y/N]: " %
                         dest_path) != "y":
                    continue
                self._remove_path(dest_path)
            self._link_path(src_path, dest_path)


class SudoSymlinkRequirement(SymlinkRequirement):
    def _remove_path(self, path):
        run(f"sudo rm {path}")

    def _link_path(self, src_path, dest_path):
        run(f"sudo ln -s {src_path} {dest_path}")


class SudoCopyRequirement(Requirement):
    def _get_paths():
        # Should yield (src, dest) pairs
        raise NotImplementedError()

    def _copy_path(src_path, dest_path):
        os.symlink(src_path, dest_path)

    def is_satisfied(self):
        for src_path, dest_path in self._get_paths():
            assert os.path.exists(src_path), "%s doesn't exist" % src_path
            if not os.path.exists(dest_path):
                return False
            if not filecmp.cmp(src_path, dest_path):
                return False
        return True

    def install(self):
        for src_path, dest_path in self._get_paths():
            if os.path.lexists(dest_path):
                run(f"sudo rm {dest_path}")
            run(f"sudo cp {src_path} {dest_path}")


class UrlInstallRequirement(Requirement):
    def url(self) -> str:
        raise NotImplementedError()

    def install(self):
        import urllib.request
        filename, _ = urllib.request.urlretrieve(self.url())
        run("chmod u+x %s" % filename)
        run_shell(filename)


class BrewBundle(Requirement):
    def is_satisfied(self):
        ret = run_silent("brew bundle check")
        return ret.returncode == 0

    def install(self):
        run("brew bundle -v")


class BrewAnalytics(Requirement):
    def is_satisfied(self):
        ret = run_silent("brew analytics state")
        return "disabled" in ret.stdout.decode("utf-8")

    def install(self):
        run("brew analytics off")


class Pip3(Requirement):
    packages = {
        "ipython"
    }

    def is_satisfied(self):
        import json
        ret = run_silent("pip3 list --format=json")
        json = json.loads(ret.stdout.decode("utf-8"))
        missing = self.packages - set(row["name"] for row in json)
        return not missing

    def install(self):
        run("pip3 install %s" % " ".join(self.packages))


class OhMyZsh(UrlInstallRequirement):
    def url(self):
        return "https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh"

    def is_satisfied(self):
        return os.path.exists(OH_MY_ZSH_DIR)


class OhMyZshCustomPlugins(SymlinkRequirement):
    def _get_paths(self):
        source_dir = os.path.join(SRC_DIR, "zsh/custom/plugins")
        for plugin in os.listdir(source_dir):
            yield os.path.join(source_dir, plugin), \
                os.path.join(OH_MY_ZSH_DIR, "custom/plugins", plugin)


class VSCodeSyncing(SymlinkRequirement):
    def _get_paths(self):
        for filename in ["settings.json", "keybindings.json", "snippets"]:
            yield (os.path.join(SRC_DIR, "Code/User/" + filename),
                   os.path.join(HOME_DIR, "Library/Application Support/Code/"
                                "User/" + filename))


class VSCodeExtensions(Requirement):
    extensions = {
        "akamud.vscode-theme-onelight",
        "andrewmarkle.primer-light",
        "awesomektvn.scratchpad",
        "bungcip.better-toml",
        "Dart-Code.dart-code",
        "Dart-Code.flutter",
        "dbaeumer.vscode-eslint",
        "eamodio.gitlens",
        "esbenp.prettier-vscode",
        "GrapeCity.gc-excelviewer",
        "johnpapa.vscode-peacock",
        "ldcf4.jumpprotobuf",
        "mauve.terraform",
        "mrmlnc.vscode-less",
        "ms-python.python",
        "ms-vscode.sublime-keybindings",
        "msjsdiag.debugger-for-chrome",
        "rust-lang.rust",
        "sharat.vscode-brewfile",
        "stkb.rewrap",
        "sysoev.vscode-open-in-github",
        "uloco.theme-bluloco-light",
        "vscode-icons-team.vscode-icons",
        "zxh404.vscode-proto3",
    }

    def _test(self):
        ret = run_silent("code --list-extensions")
        installed = set(ret.stdout.decode("utf-8").splitlines())
        missing = self.extensions - installed
        extra = installed - self.extensions
        return missing, extra

    def is_satisfied(self):
        missing, extra = self._test()
        return not missing and not extra

    def install(self):
        missing, extra = self._test()
        for extension in missing:
            run(f"code --install-extension {extension}")
        for extension in extra:
            run(f"code --uninstall-extension {extension}")


class FuzzyFinder(Requirement):
    def is_satisfied(self):
        return os.path.exists(os.path.join(HOME_DIR, ".fzf.zsh"))

    def install(self):
        run_shell(os.path.join(BREW_DIR, "opt/fzf/install"))


class DepotTools(Requirement):
    path = os.path.join(HOME_DIR, "depot_tools")

    def is_satisfied(self):
        return os.path.exists(self.path)

    def install(self):
        run(
            f"git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git {self.path}")


class Dotfiles(SymlinkRequirement):
    def _get_paths(self):
        if not os.path.exists(HYPERLOCAL_SHRC):
            run(f"touch {HYPERLOCAL_SHRC}")

        filenames = [
            HYPERLOCAL_SHRC,
            ".shrc",
            ".bashrc",
            ".zshrc",
            ".slate.js",
            ".updatelaptop",
            ".gitconfig",
        ]
        for filename in filenames:
            src_path = os.path.join(SRC_DIR, filename)
            dest_path = os.path.join(HOME_DIR, filename)
            yield src_path, dest_path


class GitWebCss(SudoCopyRequirement):
    def _get_paths(self):
        return [
            ("gitweb-common.conf", "/etc/gitweb-common.conf"),
            ("gitweb-custom.css", "/Applications/Xcode.app/Contents/Developer/usr/share/gitweb/static/gitweb-custom.css"),
            ("gitweb-custom.css", "/usr/local/opt/git/share/gitweb/static/gitweb-custom.css"),
        ]


class KarabinerSyncing(SymlinkRequirement):
    def _get_paths(self):
        yield (os.path.join(HOME_DIR, "Dropbox/karabiner"),
               os.path.join(HOME_DIR, ".config/karabiner"))


class Nvm(UrlInstallRequirement):
    def url(self):
        return "https://raw.githubusercontent.com/nvm-sh/nvm/v0.34.0/install.sh"

    def is_satisfied(self):
        return os.path.exists(NVM_DIR)


class Node(Requirement):
    versions = [
        "12",
        "10.16.0",
        "10.15.0",
    ]

    def run_nvm(self, command, silent=False):
        nvm_sh = os.path.join(NVM_DIR, "nvm.sh")
        return subprocess.run(f"source {nvm_sh}; nvm {command}",
                              shell=True,
                              stdout=subprocess.PIPE if silent else None,
                              stderr=subprocess.PIPE if silent else None)

    def is_satisfied(self):
        for version in self.versions:
            ret = self.run_nvm(f"ls {version}", silent=True)
            if ret.returncode != 0:
                return False
        return True

    def install(self):
        for version in self.versions:
            self.run_nvm(f"install {version}")
        self.run_nvm(f"use {self.versions[-1]}")


class iTerm2DynamicProfiles(SymlinkRequirement):
    def _get_paths(self):
        yield (os.path.join(HOME_DIR, "Dropbox/iTerm2DynamicProfiles/profiles.json"),
               os.path.join(HOME_DIR, "Library/Application Support/iTerm2/DynamicProfiles/profiles.json"))


def run_requirement(requirement):
    try:
        if requirement.is_satisfied():
            print("✨ %s" % requirement)
            return True

        print("🥚 %s" % requirement)
        if not DRY_RUN:
            requirement.install()

        return requirement.is_satisfied()
    except Exception as e:
        print(f"❗️ Exception encountered in '{requirement}': {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    requirements = [
        Dotfiles(),
        BrewBundle(),
        BrewAnalytics(),
        FuzzyFinder(),
        DepotTools(),
        GitWebCss(),
        KarabinerSyncing(),
        Pip3(),
        OhMyZsh(),
        OhMyZshCustomPlugins(),
        VSCodeSyncing(),
        VSCodeExtensions(),
        Nvm(),
        Node(),
        iTerm2DynamicProfiles(),
    ]

    if len(sys.argv) > 1:
        whitelist = set(sys.argv[1:])
        requirements = filter(
            lambda r: r.__class__.__name__ in whitelist, requirements)

    results = list(map(run_requirement, requirements))

    if not all(results):
        print("🚨 Some requirements still failed:")
        for requirement, result in zip(requirements, results):
            if not result:
                print("  ", requirement)
        sys.exit(1)


if __name__ == "__main__":
    main()
