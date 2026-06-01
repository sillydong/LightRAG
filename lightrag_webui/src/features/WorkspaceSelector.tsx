import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { CheckIcon, ChevronsUpDownIcon, PlusIcon } from 'lucide-react'
import Button from '@/components/ui/Button'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/Command'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/Popover'
import { getWorkspaces } from '@/api/lightrag'
import { cn } from '@/lib/utils'
import { toast } from 'sonner'

export default function WorkspaceSelector() {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const [workspaces, setWorkspaces] = useState<string[]>([])
  const [inputValue, setInputValue] = useState('')
  const [defaultWorkspace, setDefaultWorkspace] = useState('')
  const [currentWorkspace, setCurrentWorkspace] = useState(
    () => localStorage.getItem('LIGHTRAG-WORKSPACE') || ''
  )
  const didFetch = useRef(false)

  useEffect(() => {
    if (didFetch.current) return
    didFetch.current = true
    getWorkspaces()
      .then((data) => {
        setWorkspaces(data.workspaces)
        setDefaultWorkspace(data.default)
      })
      .catch(() => {
        // If the endpoint isn't available yet, keep list empty
      })
  }, [])

  const switchTo = (value: string) => {
    const trimmed = value.trim()
    if (trimmed) {
      localStorage.setItem('LIGHTRAG-WORKSPACE', trimmed)
    } else {
      localStorage.removeItem('LIGHTRAG-WORKSPACE')
    }
    setCurrentWorkspace(trimmed)
    setOpen(false)
    setInputValue('')
    toast.success(t('header.workspaceSwitched', 'Workspace switched'))
    // Reload so all data re-fetches under the new workspace
    setTimeout(() => window.location.reload(), 300)
  }

  // Workspace to display on the trigger button
  const displayLabel = currentWorkspace || defaultWorkspace || t('header.defaultWorkspace', 'default')

  // Whether the typed value is a brand-new workspace
  const trimmedInput = inputValue.trim()
  const isNew =
    trimmedInput.length > 0 &&
    !workspaces.some((w) => w.toLowerCase() === trimmedInput.toLowerCase())

  // Validate characters (same rule as backend)
  const inputInvalid = trimmedInput.length > 0 && !/^[a-zA-Z0-9_]+$/.test(trimmedInput)

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 gap-1 px-2 text-xs font-normal"
          tooltip={t('header.switchWorkspace', 'Switch Workspace')}
          side="bottom"
        >
          <span className="max-w-[80px] truncate">{displayLabel}</span>
          <ChevronsUpDownIcon className="size-3 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="w-52 p-0"
        align="end"
        sideOffset={6}
        avoidCollisions
      >
        <Command shouldFilter={false}>
          <CommandInput
            placeholder={t('header.workspacePlaceholder', 'Search or create...')}
            value={inputValue}
            onValueChange={setInputValue}
            className={cn(inputInvalid && 'text-destructive')}
          />
          {inputInvalid && (
            <p className="px-3 pb-1 text-xs text-destructive">
              {t('header.workspaceInvalidChars', 'Only letters, numbers and _ allowed')}
            </p>
          )}
          <CommandList>
            {/* Filtered existing workspaces */}
            <CommandGroup>
              {workspaces
                .filter((w) =>
                  trimmedInput.length === 0 ||
                  w.toLowerCase().includes(trimmedInput.toLowerCase())
                )
                .map((w) => {
                  const label = w || defaultWorkspace || t('header.defaultWorkspace', 'default')
                  return (
                    <CommandItem
                      key={w}
                      value={w}
                      onSelect={() => switchTo(w)}
                      className="gap-2"
                    >
                      <CheckIcon
                        className={cn(
                          'size-4 shrink-0',
                          currentWorkspace === w ? 'opacity-100' : 'opacity-0'
                        )}
                      />
                      <span className="truncate">{label}</span>
                    </CommandItem>
                  )
                })}
              {workspaces.filter((w) =>
                trimmedInput.length === 0 ||
                w.toLowerCase().includes(trimmedInput.toLowerCase())
              ).length === 0 && !isNew && (
                <CommandEmpty>
                  {t('header.noWorkspaces', 'No workspaces found')}
                </CommandEmpty>
              )}
            </CommandGroup>

            {/* Create new workspace option */}
            {isNew && !inputInvalid && (
              <>
                <CommandSeparator />
                <CommandGroup>
                  <CommandItem
                    value={`__create__${trimmedInput}`}
                    onSelect={() => switchTo(trimmedInput)}
                    className="gap-2 text-emerald-600 dark:text-emerald-400"
                  >
                    <PlusIcon className="size-4 shrink-0" />
                    <span>
                      {t('header.createWorkspace', 'Create')} &ldquo;{trimmedInput}&rdquo;
                    </span>
                  </CommandItem>
                </CommandGroup>
              </>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
